<template>
  <transition name="suggestions">
    <div v-if="show" class="search-suggestions" @click.stop>
      <!-- Скелетоны при загрузке -->
      <div v-if="isLoading" class="suggestions-loading">
        <div v-for="i in 4" :key="i" class="skeleton-row">
          <div class="skeleton-block thumb"></div>
          <div class="skeleton-lines">
            <div class="skeleton-block line w80"></div>
            <div class="skeleton-block line w45"></div>
          </div>
        </div>
      </div>

      <template v-else>
        <div class="suggestions-scroll" ref="scrollRef">
          <div
            v-for="category in enabledCategories"
            :key="category.id"
            v-show="catResults(category).length"
            class="suggestions-section"
          >
            <div class="suggestions-section-title">
              <svg
                v-if="category.id === 'anime'"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <rect x="2" y="2" width="20" height="20" rx="3" />
                <path d="M12 2v20M2 12h20" />
              </svg>
              <svg
                v-else-if="category.id === 'users'"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
              <svg
                v-else-if="category.id === 'playlists'"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M9 18V5l12-2v13" />
                <circle cx="6" cy="18" r="3" />
                <circle cx="18" cy="16" r="3" />
              </svg>
              <svg
                v-else
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M17 21v-2a4 4 0 0 0-3-5.74" />
                <path d="M9 21v-2a4 4 0 0 1 4-4" />
                <circle cx="9" cy="7" r="4" />
                <circle cx="17" cy="5" r="2" />
              </svg>
              <span class="section-name">{{ category.name }}</span>
              <span class="section-count">{{ catResults(category).length }}</span>
            </div>

            <div
              v-for="(item, index) in catResults(category)"
              :key="item.id ?? index"
              :class="[
                'suggestion-item',
                { active: selectedIndex === getGlobalIndex(category.id, index) },
              ]"
              @click="handleSelect(category.id, item)"
              @mouseenter="selectedIndex = getGlobalIndex(category.id, index)"
            >
              <!-- Аниме -->
              <div v-if="category.id === 'anime'" class="suggestion-content">
                <div class="suggestion-poster">
                  <img
                    v-if="posterUrl(getAnimePoster(item))"
                    :src="posterUrl(getAnimePoster(item))"
                    :alt="animeTitle(item)"
                    loading="lazy"
                    @error="hideImg"
                  />
                  <div v-else class="media-placeholder">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <rect x="2" y="2" width="20" height="20" rx="3" />
                      <path d="M12 2v20M2 12h20" />
                    </svg>
                  </div>
                </div>
                <div class="suggestion-info">
                  <span class="suggestion-title">
                    <HighlightText :text="animeTitle(item)" :query="query" />
                  </span>
                  <span class="suggestion-meta">
                    <span v-if="getAnimeYear(item)" class="meta-chip">{{ getAnimeYear(item) }}</span>
                    <span v-if="kindText(item)" class="meta-chip kind">
                      {{ kindText(item) }}
                    </span>
                    <span v-if="getAnimeEpisodes(item)" class="meta-chip">
                      {{ getAnimeEpisodes(item) }} эп.
                    </span>
                    <span v-if="getAnimeScore(item)" class="meta-chip score">
                      <svg
                        width="10"
                        height="10"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                      >
                        <polygon
                          points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
                        />
                      </svg>
                      {{ Number(getAnimeScore(item)).toFixed(1) }}
                    </span>
                  </span>
                </div>
              </div>

              <!-- Пользователь -->
              <div v-else-if="category.id === 'users'" class="suggestion-content">
                <span class="suggestion-avatar">
                  <img
                    v-if="posterUrl(getUserAvatar(item))"
                    :src="posterUrl(getUserAvatar(item))"
                    :alt="userTitle(item)"
                    loading="lazy"
                    @error="hideImg"
                  />
                  <span v-else class="avatar-placeholder">
                    {{ initial(userTitle(item)) }}
                  </span>
                </span>
                <div class="suggestion-info">
                  <span class="suggestion-title">
                    <HighlightText :text="userTitle(item)" :query="query" />
                  </span>
                  <span class="suggestion-meta">
                    <span class="meta-chip handle">@{{ getUserUsername(item) }}</span>
                  </span>
                </div>
              </div>

              <!-- Плейлист -->
              <div v-else-if="category.id === 'playlists'" class="suggestion-content">
                <div class="suggestion-poster playlist">
                  <img
                    v-if="playlistPoster(item)"
                    :src="posterUrl(playlistPoster(item))"
                    :alt="getPlaylistTitle(item)"
                    loading="lazy"
                    @error="hideImg"
                  />
                  <div v-else class="media-placeholder">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path d="M9 18V5l12-2v13" />
                      <circle cx="6" cy="18" r="3" />
                      <circle cx="18" cy="16" r="3" />
                    </svg>
                  </div>
                  <span class="playlist-count">{{ playlistCount(item) }}</span>
                </div>
                <div class="suggestion-info">
                  <span class="suggestion-title">
                    <HighlightText :text="getPlaylistTitle(item)" :query="query" />
                  </span>
                  <span class="suggestion-meta">
                    <span class="meta-chip handle">
                      Плейлист · {{ playlistCount(item) }} аниме
                    </span>
                  </span>
                </div>
              </div>

              <!-- Группа -->
              <div v-else class="suggestion-content">
                <span class="suggestion-avatar group">
                  <img
                    v-if="posterUrl(getGroupAvatar(item))"
                    :src="posterUrl(getGroupAvatar(item))"
                    :alt="getGroupName(item)"
                    loading="lazy"
                    @error="hideImg"
                  />
                  <span v-else class="avatar-placeholder group">
                    {{ initial(getGroupName(item)) }}
                  </span>
                </span>
                <div class="suggestion-info">
                  <span class="suggestion-title">
                    <HighlightText :text="getGroupName(item)" :query="query" />
                  </span>
                  <span class="suggestion-meta">
                    <span class="meta-chip handle">
                      {{ getGroupMembersCount(item) }} участников
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Пустой результат -->
          <div v-if="!hasResults" class="suggestions-empty">
            <svg
              width="30"
              height="30"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.6"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
              <line x1="8" y1="11" x2="14" y2="11" />
            </svg>
            <p class="empty-title">Ничего не найдено</p>
            <p class="empty-sub">Попробуйте изменить запрос</p>
          </div>
        </div>

        <!-- Футер: все результаты -->
        <router-link
          v-if="showAllLink"
          :to="{
            path: searchRoute,
            query: { [searchQueryKey]: query },
          }"
          class="suggestions-footer"
          @click="emit('close')"
        >
          <span class="footer-title">Все результаты по запросу</span>
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </router-link>
      </template>
    </div>
  </transition>
</template>

<script setup lang="ts">
import {
  ref,
  computed,
  watch,
  onMounted,
  onUnmounted,
  defineComponent,
  h,
} from "vue";
import { getMediaUrl } from "@/api/client";
import {
  type SearchResults,
  type SearchCategory,
  type AnimeResult,
  type UserResult,
  type PlaylistResult,
  type GroupResult,
} from "@/composables/useSearch";

interface Props {
  show: boolean;
  results: SearchResults;
  isLoading: boolean;
  categories?: SearchCategory[];
  query?: string;
  searchRoute?: string;
  searchQueryKey?: string;
}

const props = withDefaults(defineProps<Props>(), {
  categories: () => [],
  query: "",
  searchRoute: "/anime",
  searchQueryKey: "search",
});

const emit = defineEmits<{
  close: [];
  select: [type: string, item: unknown];
}>();

const selectedIndex = ref(-1);
const scrollRef = ref<HTMLElement | null>(null);

const enabledCategories = computed(() =>
  props.categories.filter((cat) => cat.enabled),
);

const catResults = (category: SearchCategory):
  | AnimeResult[]
  | UserResult[]
  | PlaylistResult[]
  | GroupResult[] =>
  (props.results[category.id as keyof SearchResults] || []) as
    | AnimeResult[]
    | UserResult[]
    | PlaylistResult[]
    | GroupResult[];

const hasResults = computed(() =>
  Object.values(props.results).some((arr) => arr && arr.length > 0),
);

const showAllLink = computed(
  () => hasResults.value && props.query.trim().length >= 2,
);

const totalItems = computed(() =>
  enabledCategories.value.reduce(
    (total, cat) => total + catResults(cat).length,
    0,
  ),
);

const getGlobalIndex = (categoryId: string, index: number) => {
  let globalIndex = 0;
  for (const cat of enabledCategories.value) {
    if (cat.id === categoryId) return globalIndex + index;
    globalIndex += catResults(cat).length;
  }
  return index;
};

watch(selectedIndex, (idx) => {
  if (idx < 0 || !scrollRef.value) return;
  const active = scrollRef.value.querySelector(".suggestion-item.active");
  if (active) {
    active.scrollIntoView({ block: "nearest" });
  }
});

const handleKeydown = (e: KeyboardEvent) => {
  if (!props.show) return;
  if (e.key === "ArrowDown") {
    e.preventDefault();
    selectedIndex.value = Math.min(
      selectedIndex.value + 1,
      totalItems.value - 1,
    );
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    selectedIndex.value = Math.max(selectedIndex.value - 1, 0);
  } else if (e.key === "Enter" && selectedIndex.value >= 0) {
    e.preventDefault();
    let currentIndex = 0;
    for (const cat of enabledCategories.value) {
      const items = catResults(cat);
      if (items && currentIndex + items.length > selectedIndex.value) {
        handleSelect(cat.id, items[selectedIndex.value - currentIndex]);
        return;
      }
      currentIndex += items.length;
    }
  } else if (e.key === "Escape") {
    emit("close");
  }
};

watch(
  () => props.show,
  (newShow) => {
    if (newShow) selectedIndex.value = -1;
  },
);

onMounted(() => document.addEventListener("keydown", handleKeydown));
onUnmounted(() => document.removeEventListener("keydown", handleKeydown));

const handleSelect = (type: string, item: unknown) => {
  emit("select", type, item);
  emit("close");
};

const isAnimeResult = (
  item: AnimeResult | UserResult | PlaylistResult | GroupResult,
): item is AnimeResult =>
  "poster_url" in item && ("year" in item || "episodes" in item || "score" in item);

const isUserResult = (
  item: AnimeResult | UserResult | PlaylistResult | GroupResult,
): item is UserResult =>
  "username" in item;

const isPlaylistResult = (
  item: AnimeResult | UserResult | PlaylistResult | GroupResult,
): item is PlaylistResult =>
  "title" in item && "items" in item;

const isGroupResult = (
  item: AnimeResult | UserResult | PlaylistResult | GroupResult,
): item is GroupResult =>
  "name" in item && "members_count" in item;

const posterUrl = (url?: string) => getMediaUrl(url);

const hideImg = (e: Event) => {
  (e.target as HTMLImageElement).style.display = "none";
};

const initial = (name?: string) => (
  name?.trim()?.[0]?.toUpperCase() || "?"
);

const animeTitle = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): string => {
  if (isAnimeResult(item)) return item.title_ru || item.title_en || "Без названия";
  return "Без названия";
};

const userTitle = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): string => {
  if (isUserResult(item)) return item.display_name || item.username || "Пользователь";
  return "Пользователь";
};

const animeKindMap: Record<string, string> = {
  tv: "ТВ",
  movie: "Фильм",
  ova: "OVA",
  ona: "ONA",
  special: "Спешл",
  music: "Музыка",
  cm: "CM",
  tv_special: "ТВ спешл",
};

const kindText = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): string | null => {
  if (isAnimeResult(item) && item.kind) {
    return animeKindMap[item.kind] || item.kind;
  }
  return null;
};

const playlistPoster = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): string | undefined => {
  if (!isPlaylistResult(item)) return undefined;
  const list: Array<Record<string, unknown>> = Array.isArray(item.items)
    ? (item.items as Array<Record<string, unknown>>)
    : [];
  for (const entry of list) {
    const p =
      entry.anime_poster ||
      entry.anime_poster_url ||
      ((entry.anime as Record<string, unknown> | undefined)?.poster_url as
        string
        | undefined);
    if (p) return String(p);
  }
  return undefined;
};

const playlistCount = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): number => {
  if (!isPlaylistResult(item)) return 0;
  const n =
    (item as PlaylistResult & { items_count?: number }).items_count ??
    (Array.isArray(item.items) ? item.items.length : 0);
  return n || 0;
};

const getAnimePoster = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): string | undefined => {
  if (isAnimeResult(item)) return item.poster_url;
  return undefined;
};

const getAnimeYear = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): number | undefined => {
  if (isAnimeResult(item)) return item.year;
  return undefined;
};

const getAnimeEpisodes = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): number | undefined => {
  if (isAnimeResult(item)) return item.episodes;
  return undefined;
};

const getAnimeScore = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): number | undefined => {
  if (isAnimeResult(item)) return item.score;
  return undefined;
};

const getUserAvatar = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): string | undefined => {
  if (isUserResult(item)) return item.avatar_url;
  return undefined;
};

const getUserUsername = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): string => {
  if (isUserResult(item)) return item.username;
  return "";
};

const getPlaylistTitle = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): string => {
  if (isPlaylistResult(item)) return item.title;
  return "";
};

const getGroupAvatar = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): string | undefined => {
  if (isGroupResult(item)) return item.avatar_url;
  return undefined;
};

const getGroupName = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): string => {
  if (isGroupResult(item)) return item.name;
  return "";
};

const getGroupMembersCount = (item: AnimeResult | UserResult | PlaylistResult | GroupResult): number => {
  if (isGroupResult(item)) return item.members_count || 0;
  return 0;
};

const HighlightText = defineComponent({
  name: "HighlightText",
  props: {
    text: { type: String, default: "" },
    query: { type: String, default: "" },
  },
  setup(props) {
    return () => {
      const text = String(props.text ?? "");
      const query = String(props.query ?? "").trim();
      if (!query) return text;
      const lower = text.toLowerCase();
      const idx = lower.indexOf(query.toLowerCase());
      if (idx === -1) return text;
      const tail = text.slice(idx + query.length);
      return [
        text.slice(0, idx),
        h("mark", { class: "hl-match" }, text.slice(idx, idx + query.length)),
        tail,
      ];
    };
  },
});
</script>

<style scoped>
.search-suggestions {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  width: 100%;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(180deg, var(--surface-3) 0%, var(--surface-2) 100%);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg), var(--shadow-glow-sm);
  overflow: hidden;
  max-height: 520px;
  z-index: var(--z-dropdown);
  animation: suggestionsPop 0.16s var(--ease-bloom);
}

@keyframes suggestionsPop {
  from {
    opacity: 0;
    transform: translateY(-6px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.suggestions-scroll {
  overflow-y: auto;
  overflow-x: hidden;
  padding: 6px;
}

/* ---- Секции ---- */
.suggestions-section {
  margin-bottom: 2px;
}
.suggestions-section:not(:last-child) {
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 6px;
  margin-bottom: 6px;
}

.suggestions-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px 6px 6px;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.suggestions-section-title svg {
  color: var(--accent);
  flex-shrink: 0;
}
.section-count {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: var(--radius-full);
  background: var(--surface-4);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0;
}

/* ---- Элемент подсказки (единая высота строки) ---- */
.suggestion-item {
  display: block;
  padding: 6px;
  margin: 0;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition:
    background-color var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out);
}
.suggestion-item:hover,
.suggestion-item.active {
  background-color: var(--surface-4);
  box-shadow: inset 0 0 0 1px var(--border-subtle);
}
.suggestion-item.active {
  background-color: var(--accent-subtle);
  box-shadow: inset 0 0 0 1px var(--accent-glow-sm);
}

.suggestion-content {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 62px;
  width: 100%;
}

/* ---- Постеры и аватары ---- */
.suggestion-poster {
  width: 42px;
  height: 63px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background-color: var(--surface-4);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-sm);
}
.suggestion-poster.playlist {
  box-shadow: var(--shadow-sm), 0 0 0 1px var(--border-subtle);
}
.suggestion-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.suggestion-poster.playlist img {
  object-fit: cover;
}

.media-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

.playlist-count {
  position: absolute;
  right: 3px;
  bottom: 3px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background: rgba(10, 8, 18, 0.82);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  backdrop-filter: blur(4px);
}

.suggestion-avatar {
  width: 42px;
  height: 42px;
  flex-shrink: 0;
  border-radius: var(--radius-full);
  overflow: hidden;
  background:
    radial-gradient(circle at 30% 20%, var(--surface-6), var(--surface-3));
  box-shadow: var(--shadow-sm);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.suggestion-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.suggestion-avatar.group {
  background:
    radial-gradient(circle at 30% 25%, var(--accent-2-subtle), var(--surface-3));
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-bright);
  font-size: var(--text-lg);
  font-weight: 700;
  background: linear-gradient(
    135deg,
    var(--accent-subtle) 0%,
    var(--surface-5) 100%
  );
}
.avatar-placeholder.group {
  color: var(--accent-2);
  background: linear-gradient(
    135deg,
    var(--accent-2-subtle) 0%,
    var(--surface-5) 100%
  );
}

/* ---- Инфо ---- */
.suggestion-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}

.suggestion-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hl-match {
  background: var(--accent-subtle);
  color: var(--accent-bright);
  border-radius: 3px;
  padding: 0 1px;
}

.suggestion-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 7px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
  line-height: 1.6;
  color: var(--text-secondary);
  background: var(--surface-4);
}
.meta-chip.kind {
  text-transform: uppercase;
  font-size: 10px;
  font-weight: 700;
  color: var(--accent-bright);
  background: var(--accent-subtle);
  letter-spacing: 0.03em;
}
.meta-chip.score {
  color: var(--warning);
  font-weight: 600;
  background: var(--warning-subtle);
}
.meta-chip.score svg {
  width: 10px;
  height: 10px;
}
.meta-chip.handle {
  color: var(--text-tertiary);
  background: transparent;
  padding: 0;
}

/* ---- Пустой результат ---- */
.suggestions-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: var(--space-8) var(--space-6);
  color: var(--text-tertiary);
  text-align: center;
}
.suggestions-empty svg {
  opacity: 0.5;
  margin-bottom: 6px;
}
.empty-title {
  margin: 0;
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-secondary);
}
.empty-sub {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

/* ---- Загрузка (скелетоны) ---- */
.suggestions-loading {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.skeleton-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 5px 6px;
  min-height: 62px;
}
.skeleton-block {
  background: linear-gradient(
    90deg,
    var(--surface-4) 25%,
    var(--surface-5) 50%,
    var(--surface-4) 75%
  );
  background-size: 400% 100%;
  animation: shimmer 1.4s var(--ease-inout) infinite;
  border-radius: var(--radius-sm);
}
.skeleton-block.thumb {
  width: 42px;
  height: 63px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
}
.skeleton-lines {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.skeleton-block.line {
  height: 11px;
  border-radius: var(--radius-full);
}
.skeleton-block.w80 {
  width: 80%;
}
.skeleton-block.w45 {
  width: 45%;
}

@keyframes shimmer {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

/* ---- Футер ---- */
.suggestions-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px solid var(--border-default);
  background: var(--surface-3);
  color: var(--accent-bright);
  font-size: var(--text-sm);
  font-weight: 600;
  text-decoration: none;
  transition:
    background-color var(--duration-fast) var(--ease-out),
    color var(--duration-fast) var(--ease-out);
}
.suggestions-footer:hover {
  background: var(--accent-subtle);
  color: var(--accent-bright);
}
.suggestions-footer svg {
  flex-shrink: 0;
  opacity: 0.8;
}
</style>