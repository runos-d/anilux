<template>
  <div class="playlist-detail-page">
    <div v-if="loading" class="detail-loading">
      <div class="loading-cover-skeleton"></div>
      <div class="loading-info-skeleton">
        <div class="sk-line w-60"></div>
        <div class="sk-line w-40"></div>
        <div class="sk-line w-80"></div>
        <div class="sk-actions">
          <div class="sk-btn"></div>
          <div class="sk-btn"></div>
          <div class="sk-btn"></div>
        </div>
      </div>
    </div>

    <div v-else-if="!playlist" class="not-found">
      <div class="not-found-icon"><SakuraIcon name="music" /></div>
      <h2>Плейлист не найден</h2>
      <p>Возможно, он был удалён или у вас нет доступа</p>
      <router-link :to="returnToPlaylists" class="btn-back-link"
        ><SakuraIcon name="arrow-left" :size="16" /> Все плейлисты</router-link
      >
    </div>

    <template v-else>
      <div class="breadcrumb">
        <router-link :to="returnToPlaylists" class="breadcrumb-link">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Все плейлисты
        </router-link>
      </div>

      <div class="playlist-hero">
        <div class="hero-cover">
          <PlaylistCover :posters="coverItems.map(item => item.anime_poster)" :custom-cover="playlist.cover_image" :label="`Обложка: ${playlist.title}`" priority />
          <div
            class="privacy-hero-badge"
            :class="`privacy-${currentVisibility}`"
          >
            <SakuraIcon :name="privacyIcon" :size="12" /> {{ privacyLabel }}
          </div>
        </div>

        <div class="hero-info">
          <h1 class="hero-title">{{ seoPage?.status === 200 ? seoPage.h1 : playlist.title }}</h1>
          <div class="hero-meta">
            <div class="author-chip" @click="goToAuthor">
              <img
                v-if="playlist.user_avatar && !authorAvatarFailed"
                :src="getMediaUrl(playlist.user_avatar)"
                class="author-chip-avatar"
                loading="lazy"
                @error="authorAvatarFailed = true"
              />
              <div v-else class="author-chip-avatar-ph">
                {{ (playlist.user_username || "?")[0]?.toUpperCase() ?? "?" }}
              </div>
              <span>{{ playlist.user_username }}</span>
            </div>
            <span class="meta-dot">·</span>
            <span class="meta-item">
              <svg
                width="13"
                height="13"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <rect x="2" y="7" width="20" height="14" rx="2" />
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
              </svg>
              {{ playlist.items_count }} аниме
            </span>
            <span class="meta-dot">·</span>
            <span class="meta-item">
              <svg
                width="13"
                height="13"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <rect x="3" y="4" width="18" height="18" rx="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              {{ formatDate(playlist.created_at) }}
            </span>
          </div>

          <div class="hero-actions">
            <button
              class="action-hero-btn primary"
              :disabled="!sortedItems.length"
              @click="watchPlaylist"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Смотреть плейлист
            </button>
            <button
              @click="toggleFavorite"
              :class="['action-hero-btn', { active: playlist.is_favorited }]"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                :fill="playlist.is_favorited ? 'currentColor' : 'none'"
                stroke="currentColor"
                stroke-width="2"
              >
                <polygon
                  points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
                />
              </svg>
              {{ playlist.is_favorited ? "В избранном" : "В избранное" }}
            </button>

            <button @click="sharePlaylist" class="action-hero-btn">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <circle cx="18" cy="5" r="3" />
                <circle cx="6" cy="12" r="3" />
                <circle cx="18" cy="19" r="3" />
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
              </svg>
              Поделиться
            </button>

            <button @click="copyAllLinks" class="action-hero-btn">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <rect x="9" y="9" width="13" height="13" rx="2" />
                <path
                  d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                />
              </svg>
              Ссылки
            </button>

            <template v-if="isOwner">
              <!-- <button
                @click="showAddAnimeModal = true"
                class="action-hero-btn primary"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                >
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                Добавить
              </button> -->
              <button @click="openEditPage" class="action-hero-btn">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                  />
                  <path
                    d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
                  />
                </svg>
                Изменить
              </button>
              <button @click="openExportModal()" class="action-hero-btn">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Экспорт
              </button>
              <button
                @click="showDeleteConfirm = true"
                class="action-hero-btn danger"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <polyline points="3 6 5 6 21 6" />
                  <path
                    d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                  />
                </svg>
                Удалить
              </button>
            </template>
          </div>

          <div class="hero-stats">
            <span class="stat-chip">
              <svg
                width="13"
                height="13"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
                />
              </svg>
              {{ playlist.favorites_count }} в избранном
            </span>
            <span v-if="totalDuration > 0" class="stat-chip">
              <svg
                width="13"
                height="13"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
              {{ formattedTotalDuration }}
            </span>
          </div>
        </div>
      </div>

      <p v-if="playlist.topics?.length" class="playlist-topic-list">Тематики: {{ playlist.topics.map(playlistTopicName).join(" · ") }}</p>
      <div v-if="playlist.description" class="description-section">
        <div class="section-label">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
            />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          Описание
        </div>
        <p class="description-text">{{ playlist.description }}</p>
      </div>

      <div class="anime-section">
        <div class="section-header">
          <div class="section-label">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <rect x="2" y="7" width="20" height="14" rx="2" />
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
            </svg>
            Аниме в плейлисте ({{ playlist.items_count }})
          </div>
          <div class="anime-controls" v-if="isOwner || sortedItems.length > 10">
            <select v-model="itemsSort" @change="onSortChange" class="sort-select-sm">
              <option value="position">По порядку</option>
              <option value="anime__title_ru">По названию (А-Я)</option>
              <option value="-anime__title_ru">По названию (Я-А)</option>
              <option value="anime__year">По году (старые)</option>
              <option value="-anime__year">По году (новые)</option>
              <option value="anime__score">По оценке (низкая)</option>
              <option value="-anime__score">По оценке (высокая)</option>
            </select>
          </div>
        </div>

        <div
          v-if="sortedItems.length === 0"
          class="anime-empty"
        >
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <rect x="2" y="7" width="20" height="14" rx="2" />
            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
          </svg>
          <p>Плейлист пока пуст</p>
          <button
            v-if="isOwner"
            @click="showAddAnimeModal = true"
            class="btn-add-empty"
          >
            Добавить аниме
          </button>
        </div>

        <div class="anime-list" ref="listRef">
          <template
            v-for="entry in listWithPlaceholder"
            :key="entry.type === 'placeholder' ? 'placeholder' : entry.data.id"
          >
            <div
              v-if="entry.type === 'placeholder'"
              class="drag-placeholder"
              :style="{ height: `${dragState.itemHeight}px` }"
            ></div>
            <div
              v-else
              class="anime-row"
              :class="[
                'anime-row',
                { 'is-dragging': dragState.activeIndex === entry.originalIndex },
              ]"
              :data-index="entry.originalIndex"
              :style="dragState.activeIndex === entry.originalIndex ? dragItemStyle : {}"
            >
              <div
                class="row-index-wrap"
                :class="{ 'is-handle': isOwner }"
                @mousedown.prevent="isOwner ? startDrag($event, entry.originalIndex) : null"
                @touchstart.prevent="
                  isOwner ? startDragTouch($event, entry.originalIndex) : null
                "
              >
                <span v-if="!isOwner" class="row-index">{{ entry.originalIndex + 1 }}</span>
                <div v-else class="drag-handle">
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2.5"
                  >
                    <circle cx="9" cy="5" r="1.2" fill="currentColor" />
                    <circle cx="9" cy="12" r="1.2" fill="currentColor" />
                    <circle cx="9" cy="19" r="1.2" fill="currentColor" />
                    <circle cx="15" cy="5" r="1.2" fill="currentColor" />
                    <circle cx="15" cy="12" r="1.2" fill="currentColor" />
                    <circle cx="15" cy="19" r="1.2" fill="currentColor" />
                  </svg>
                </div>
              </div>

              <router-link :to="`/anime/${entry.data.anime_slug || entry.data.anime}`" class="row-poster-link">
                <div class="row-poster">
                  <img
                    v-if="entry.data.anime_poster"
                    :src="getMediaUrl(entry.data.anime_poster)"
                    :alt="entry.data.anime_title"
                    loading="lazy"
                    @error="
                      (e: Event) =>
                        ((e.target as HTMLImageElement).style.display = 'none')
                    "
                  />
                  <div v-else class="row-poster-ph">
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.5"
                    >
                      <rect x="2" y="2" width="20" height="20" rx="2" />
                    </svg>
                  </div>
                </div>
              </router-link>

              <div class="row-info">
                <router-link :to="`/anime/${entry.data.anime_slug || entry.data.anime}`" class="row-title">
                  {{ entry.data.anime_title }}
                </router-link>
                <div v-if="entry.data.notes" class="row-note">
                  <svg
                    width="11"
                    height="11"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path
                      d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                    />
                  </svg>
                  {{ entry.data.notes }}
                </div>
                <div class="row-meta">
                  <span v-if="entry.data.anime_year" class="row-meta-chip">{{
                    entry.data.anime_year
                  }}</span>
                </div>
                  <div
                    class="row-progress"
                    :class="{ 'is-empty': !entry.data.user_watch_progress }"
                    :title="`${entry.data.user_watch_progress?.episodes_watched ?? 0} / ${entry.data.anime_episodes}`"
                  >
                  <div
                    class="row-progress-bar"
                    :style="{ width: `${entry.data.user_watch_progress ? entry.data.user_watch_progress.progress_percentage : 0}%` }"
                  ></div>
                </div>
              </div>

              <div class="row-actions">
                <router-link
                  :to="`/anime/${entry.data.anime_slug || entry.data.anime}/watch`"
                  class="row-action-btn play"
                  title="Смотреть"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    stroke="none"
                  >
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                </router-link>

                <button
                  @click="copyAnimeLink(entry.data)"
                  class="row-action-btn"
                  :title="
                    entry.data.source_url
                      ? 'Копировать ссылку'
                      : 'Копировать ссылку на аниме'
                  "
                >
                  <svg
                    width="13"
                    height="13"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <rect x="9" y="9" width="13" height="13" rx="2" />
                    <path
                      d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                    />
                  </svg>
                </button>

                <template v-if="isOwner">
                  <button
                    @click="openEditItem(entry.data)"
                    class="row-action-btn"
                    title="Редактировать заметку"
                  >
                    <svg
                      width="13"
                      height="13"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path
                        d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                      />
                      <path
                        d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
                      />
                    </svg>
                  </button>
                  <button
                    @click="openRemoveItem(entry.data)"
                    class="row-action-btn danger"
                    title="Удалить"
                  >
                    <svg
                      width="13"
                      height="13"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </template>
              </div>
            </div>
          </template>
        </div>

        <div v-if="totalItemsPages > 1" class="items-pagination">
          <button @click="itemsPage--" :disabled="itemsPage === 1" class="page-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <span class="page-indicator">Стр. {{ itemsPage }} / {{ totalItemsPages }}</span>
          <button @click="itemsPage++" :disabled="itemsPage === totalItemsPages" class="page-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>
      </div>
    </template>

    <Teleport to="body">
      <transition name="modal">
        <div
          v-if="showAddAnimeModal"
          class="modal-overlay"
          @click.self="showAddAnimeModal = false"
        >
          <div class="modal-box">
            <div class="modal-header">
              <h3>Добавить аниме</h3>
              <button
                @click="showAddAnimeModal = false"
                class="modal-close-btn"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="modal-search-wrap">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  class="modal-search-icon"
                >
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                <input
                  v-model="addAnimeSearch"
                  @input="debouncedAnimeSearch"
                  type="text"
                  placeholder="Название аниме..."
                  class="modal-search-input"
                  autofocus
                />
                <button
                  v-if="addAnimeSearch"
                  @click="
                    addAnimeSearch = '';
                    animeSearchResults = [];
                  "
                  class="modal-search-clear"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
              <div v-if="animeSearchLoading" class="modal-loading">
                <div class="spinner-sm"></div>
                Поиск...
              </div>
              <div
                v-else-if="animeSearchResults.length > 0"
                class="modal-results"
              >
                <div
                  v-for="anime in animeSearchResults"
                  :key="anime.id"
                  @click="addAnimeToPlaylist(anime)"
                  :class="[
                    'modal-result-item',
                    { disabled: isAnimeInPlaylist(anime.id) },
                  ]"
                >
                  <img
                    v-if="anime.poster_url"
                    :src="getMediaUrl(anime.poster_url)"
                    :alt="anime.title_ru"
                    class="modal-result-poster"
                    loading="lazy"
                    @error="
                      (e: Event) =>
                        ((e.target as HTMLImageElement).style.display = 'none')
                    "
                  />
                  <div v-else class="modal-result-poster-ph"></div>
                  <div class="modal-result-info">
                    <span class="modal-result-title">{{
                      anime.title_ru || anime.title_en
                    }}</span>
                    <span class="modal-result-meta">
                      {{ anime.year
                      }}{{
                        anime.episodes ? ` · ${anime.episodes} эп.` : ""
                      }}
                      {{ anime.score ? ` ·
                      <SakuraIcon name="star" />
                      ${Number(anime.score).toFixed(1)}` : '' }}
                    </span>
                  </div>
                  <span v-if="isAnimeInPlaylist(anime.id)" class="already-added"
                    ><SakuraIcon name="check" :size="16" /> Добавлено</span
                  >
                  <button v-else class="btn-add-anime" type="button">
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2.5"
                    >
                      <line x1="12" y1="5" x2="12" y2="19" />
                      <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                  </button>
                </div>
              </div>
              <div
                v-else-if="addAnimeSearch.length >= 2 && !animeSearchLoading"
                class="modal-empty"
              >
                Ничего не найдено по запросу «{{ addAnimeSearch }}»
              </div>
              <div v-else-if="!addAnimeSearch" class="modal-empty-hint">
                Начните вводить название аниме для поиска
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <Teleport to="body">
      <transition name="modal">
        <div
          v-if="editingItem"
          class="modal-overlay"
          @click.self="editingItem = null"
        >
          <div class="modal-box modal-box-sm">
            <div class="modal-header">
              <h3>Заметка к аниме</h3>
              <button @click="editingItem = null" class="modal-close-btn">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="anime-edit-preview">
                <img
                  v-if="editingItem.anime_poster"
                  :src="getMediaUrl(editingItem.anime_poster)"
                  class="edit-preview-poster"
                  loading="lazy"
                />
                <span class="edit-preview-title">{{
                  editingItem.anime_title
                }}</span>
              </div>
              <div class="form-group">
                <label class="form-label">Заметка</label>
                <textarea
                  v-model="editItemNotes"
                  class="form-textarea"
                  rows="3"
                  maxlength="300"
                  placeholder="Добавьте заметку..."
                ></textarea>
              </div>
            </div>
            <div class="modal-footer">
              <button @click="editingItem = null" class="btn-modal-cancel">
                Отмена
              </button>
              <button
                @click="saveItemNotes"
                :disabled="itemSaving"
                class="btn-modal-save"
              >
                {{ itemSaving ? "Сохранение..." : "Сохранить" }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <Teleport to="body">
      <transition name="modal">
        <div
          v-if="removingItem"
          class="modal-overlay"
          @click.self="removingItem = null"
        >
          <div class="modal-box modal-box-sm">
            <div class="modal-header">
              <h3>Удалить аниме?</h3>
              <button @click="removingItem = null" class="modal-close-btn">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div class="modal-body confirm-body">
              <div class="confirm-anime-row">
                <img
                  v-if="removingItem.anime_poster"
                  :src="getMediaUrl(removingItem.anime_poster)"
                  class="confirm-poster"
                  loading="lazy"
                />
                <div v-else class="confirm-poster-ph"></div>
                <span class="confirm-anime-title">{{
                  removingItem.anime_title
                }}</span>
              </div>
              <p class="confirm-text">
                Вы уверены, что хотите удалить это аниме из плейлиста?
              </p>
            </div>
            <div class="modal-footer">
              <button @click="removingItem = null" class="btn-modal-cancel">
                Отмена
              </button>
              <button @click="confirmRemoveItem" class="btn-modal-danger">
                Удалить
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <Teleport to="body">
      <transition name="modal">
        <div
          v-if="showDeleteConfirm"
          class="modal-overlay"
          @click.self="showDeleteConfirm = false"
        >
          <div class="modal-box modal-box-sm">
            <div class="modal-header">
              <h3>Удалить плейлист?</h3>
              <button
                @click="showDeleteConfirm = false"
                class="modal-close-btn"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div class="modal-body confirm-body">
              <div class="confirm-icon"><SakuraIcon name="trash" /></div>
              <p class="confirm-text">
                Вы хотите удалить плейлист<br />
                <strong>«{{ playlist?.title }}»</strong>?<br />
                Это действие необратимо.
              </p>
            </div>
            <div class="modal-footer">
              <button
                @click="showDeleteConfirm = false"
                class="btn-modal-cancel"
              >
                Отмена
              </button>
              <button
                @click="confirmDeletePlaylist"
                :disabled="isDeleting"
                class="btn-modal-danger"
              >
                <div v-if="isDeleting" class="spinner-sm-dark"></div>
                {{ isDeleting ? "Удаление..." : "Удалить навсегда" }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <Teleport to="body">
      <transition name="modal">
        <div
          v-if="showExportModal"
          class="modal-overlay"
          @click.self="showExportModal = false"
        >
          <div class="modal-box">
            <div class="modal-header">
              <h3>Экспорт плейлиста</h3>
              <button @click="showExportModal = false" class="modal-close-btn">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Формат</label>
                <div class="export-formats">
                  <label
                    v-for="fmt in exportFormats"
                    :key="fmt.value"
                    :class="[
                      'export-fmt',
                      { active: exportFormat === fmt.value },
                    ]"
                  >
                    <input
                      type="radio"
                      :value="fmt.value"
                      v-model="exportFormat"
                      style="display: none"
                    />
                    <span class="fmt-icon"><SakuraIcon :name="fmt.icon" :size="18" /></span>
                    <div>
                      <div class="fmt-label">{{ fmt.label }}</div>
                      <div class="fmt-desc">{{ fmt.desc }}</div>
                    </div>
                  </label>
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">Предпросмотр</label>
                <div class="export-preview">
                  <pre class="export-text">{{ exportPreview }}</pre>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button @click="showExportModal = false" class="btn-modal-cancel">
                Закрыть
              </button>
              <button @click="copyExport" class="btn-modal-save outline">
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <rect x="9" y="9" width="13" height="13" rx="2" />
                  <path
                    d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                  />
                </svg>
                Скопировать
              </button>
              <button @click="downloadExport" class="btn-modal-save">
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Скачать
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <Teleport to="body">
      <transition name="toast">
        <div v-if="toastMsg" class="toast-notification">
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
          {{ toastMsg }}
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { seoPage } from '@/composables/useSeo';
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { useCachedReads } from '@/composables/useCachedReads';
const read = useCachedReads();
import { ref, computed, onMounted, onUnmounted, reactive, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import PlaylistCover from "@/components/Playlists/PlaylistCover.vue";
import { playlistTopicName } from "@/lib/playlistTopics";
import playlistsApi, {
  type Playlist,
  type PlaylistItem,
  type PlaylistVisibility,
} from "@/api/playlists";
import apiClient, { getMediaUrl } from "@/api/client";
import type { AxiosError } from "axios";
import type { Anime } from "@/types";
import { TIMING } from "@/constants";
import { formatDuration } from "@/utils/normalizers";

const route = useRoute();
const returnToPlaylists = computed(() => typeof route.query.returnTo === "string" && /^\/playlists(?:\?|$)/.test(route.query.returnTo) ? route.query.returnTo : "/playlists");
const router = useRouter();
const authStore = useAuthStore();

const playlist = ref<Playlist | null>(null);
const loading = ref(true);
const currentUserId = ref<number | undefined>(undefined);
const toastMsg = ref("");
const listRef = ref<HTMLElement | null>(null);
const items = ref<PlaylistItem[]>([]);
const itemsLoading = ref(true);
const itemsPage = ref(1);
const itemsTotal = ref(0);
const itemsSort = ref<string>('position');
const ITEMS_PER_PAGE = 10;

const totalDuration = computed(() => playlist.value?.total_duration || 0);
const formattedTotalDuration = computed(() => formatDuration(totalDuration.value));

const isOwner = computed(() => {
  if (!playlist.value || !currentUserId.value) return false;
  return playlist.value.user_id === currentUserId.value;
});

const showAddAnimeModal = ref(false);
const showExportModal = ref(false);
const authorAvatarFailed = ref(false);
const exportItems = ref<PlaylistItem[]>([]);
const showDeleteConfirm = ref(false);
const editingItem = ref<PlaylistItem | null>(null);
const removingItem = ref<PlaylistItem | null>(null);
const isDeleting = ref(false);

interface DragState {
  active: boolean;
  activeIndex: number | null;
  insertIndex: number | null;
  startY: number;
  currentY: number;
  itemHeight: number;
  offsetY: number;
  draggedElement: HTMLElement | null;
  scrollTimer: number | null;
}
interface ListEntryItem {
  type: "item";
  data: PlaylistItem;
  originalIndex: number;
}
interface ListEntryPlaceholder {
  type: "placeholder";
}
type ListEntry = ListEntryItem | ListEntryPlaceholder;
const dragState = reactive<DragState>({
  active: false,
  activeIndex: null,
  insertIndex: null,
  startY: 0,
  currentY: 0,
  itemHeight: 0,
  offsetY: 0,
  draggedElement: null,
  scrollTimer: null,
});

const dragItemStyle = computed(() => {
  if (!dragState.active || dragState.activeIndex === null) return {};
  const dy = dragState.currentY - dragState.startY;
  return {
    position: "fixed" as const,
    top: `${dragState.startY - dragState.offsetY}px`,
    transform: `translateY(${dy}px)`,
    left: `${dragState.draggedElement?.getBoundingClientRect().left}px`,
    width: `${dragState.draggedElement?.offsetWidth}px`,
    height: `${dragState.itemHeight}px`,
    zIndex: "1000",
    boxShadow: "0 12px 32px rgba(0,0,0,0.45)",
    opacity: "0.92",
    transition: "none",
    willChange: "transform",
  };
});

const listWithPlaceholder = computed((): ListEntry[] => {
  if (!dragState.active || dragState.insertIndex === null) {
    return sortedItems.value.map((item, i) => ({
      type: "item" as const,
      data: item,
      originalIndex: i,
    }));
  }

  const items: ListEntry[] = sortedItems.value.map((item, i) => ({
    type: "item" as const,
    data: item,
    originalIndex: i,
  }));
  items.splice(dragState.insertIndex, 0, { type: "placeholder" as const });
  return items;
});

const startDragTouch = (e: TouchEvent, index: number) => {
  const touch = e.touches[0] || e.changedTouches[0];
  const mouseEvent = {
    clientX: touch!.clientX,
    clientY: touch!.clientY,
    preventDefault: () => e.preventDefault(),
    stopPropagation: () => e.stopPropagation(),
  } as unknown as MouseEvent;
  startDrag(mouseEvent, index);
};

const startDrag = (e: MouseEvent, index: number) => {
  if (!listRef.value) return;
  const row = listRef.value.querySelector(
    `[data-index="${index}"]`,
  ) as HTMLElement;
  if (!row) return;

  const rect = row.getBoundingClientRect();
  dragState.active = true;
  dragState.activeIndex = index;
  dragState.insertIndex = index;
  dragState.startY = e.clientY;
  dragState.currentY = e.clientY;
  dragState.itemHeight = rect.height;
  dragState.offsetY = e.clientY - rect.top;
  dragState.draggedElement = row;

  row.classList.add("is-being-dragged");

  document.addEventListener("mousemove", onDragMove, { passive: true });
  document.addEventListener("mouseup", onDragEnd);
  document.addEventListener("touchmove", onDragMoveTouch, { passive: true });
  document.addEventListener("touchend", onDragEnd);
  document.body.style.userSelect = "none";
  document.body.style.cursor = "grabbing";
};

const onDragMoveTouch = (e: TouchEvent) => {
  if (!dragState.active || dragState.activeIndex === null || !listRef.value)
    return;
  const touch = e.touches[0] || e.changedTouches[0];
  dragState.currentY = touch!.clientY;
  handleAutoScroll(touch!.clientY);
};

const handleAutoScroll = (clientY: number) => {
  if (!listRef.value) return;

  const listRect = listRef.value.getBoundingClientRect();
  const scrollZone = 60; // Зона у края для авто-скролла
  const scrollSpeed = 8; // Скорость прокрутки в пикселях

  if (dragState.scrollTimer) {
    window.clearInterval(dragState.scrollTimer);
    dragState.scrollTimer = null;
  }

  if (clientY < listRect.top + scrollZone) {
    dragState.scrollTimer = window.setInterval(() => {
      window.scrollBy(0, -scrollSpeed);
    }, 16);
  }
  else if (clientY > listRect.bottom - scrollZone) {
    dragState.scrollTimer = window.setInterval(() => {
      window.scrollBy(0, scrollSpeed);
    }, 16);
  }
};

const onDragMove = (e: MouseEvent) => {
  if (!dragState.active || dragState.activeIndex === null || !listRef.value)
    return;
  dragState.currentY = e.clientY;
  handleAutoScroll(e.clientY);

  const rows = Array.from(
    listRef.value.querySelectorAll(".anime-row:not(.is-being-dragged)"),
  ) as HTMLElement[];
  if (rows.length === 0) {
    dragState.insertIndex = dragState.activeIndex;
    return;
  }

  const rowData = rows
    .map((row) => {
      const rect = row.getBoundingClientRect();
      return {
        dataIndex: parseInt(row.dataset.index || "0", 10),
        top: rect.top,
        bottom: rect.bottom,
      };
    })
    .sort((a, b) => a.top - b.top);

  const candidates: Array<{ y: number; insertIndex: number }> = [];

  candidates.push({
    y: rowData[0]!.top,
    insertIndex: 0,
  });

  for (let i = 0; i < rowData.length - 1; i++) {
    const curr = rowData[i]!;
    const next = rowData[i + 1]!;
    candidates.push({
      y: (curr.bottom + next.top) / 2,
      insertIndex: i,
    });
  }

  candidates.push({
    y: rowData[rowData.length - 1]!.bottom,
    insertIndex: rowData.length,
  });

  let best = candidates[0]!;
  let bestDist = Math.abs(e.clientY - best.y);
  for (let i = 1; i < candidates.length; i++) {
    const dist = Math.abs(e.clientY - candidates[i]!.y);
    if (dist < bestDist) {
      bestDist = dist;
      best = candidates[i]!;
    }
  }

  const maxIndex = sortedItems.value.length;
  dragState.insertIndex = Math.max(0, Math.min(best.insertIndex, maxIndex));
};

const onDragEnd = async () => {
  if (dragState.scrollTimer) {
    window.clearInterval(dragState.scrollTimer);
    dragState.scrollTimer = null;
  }

  document.removeEventListener("mousemove", onDragMove);
  document.removeEventListener("mouseup", onDragEnd);
  document.removeEventListener("touchmove", onDragMoveTouch);
  document.removeEventListener("touchend", onDragEnd);
  document.body.style.userSelect = "";
  document.body.style.cursor = "";
  document.body.style.overflow = "";

  if (dragState.draggedElement) {
    dragState.draggedElement.classList.remove("is-being-dragged");
    dragState.draggedElement = null;
  }

  const from = dragState.activeIndex;
  const insertAt = dragState.insertIndex;

  dragState.active = false;
  dragState.activeIndex = null;
  dragState.insertIndex = null;

  if (from === null || insertAt === null || from === insertAt || !playlist.value) return;

  const items = [...sortedItems.value];
  const [moved] = items.splice(from, 1);
  if (moved) {
    items.splice(insertAt, 0, moved);
    items.forEach((item, idx) => {
      item.position = idx + 1;
    });
    playlist.value.items = items;
  }

  try {
    await playlistsApi.reorderPlaylistItems(
      playlist.value.id,
      items.map((item, idx) => ({ id: item.id, position: idx + 1 })),
    );
  } catch {
    await loadPlaylist();
  }
};

const addAnimeSearch = ref("");
const animeSearchResults = ref<Anime[]>([]);
const animeSearchLoading = ref(false);
let searchTimer: ReturnType<typeof setTimeout> | null = null;

const editItemNotes = ref("");
const itemSaving = ref(false);

const exportFormat = ref<"text" | "text_links" | "json" | "csv" | "markdown">(
  "text",
);
const exportFormats = [
  { value: "text", label: "Текст", icon: "file-text", desc: "Простой список" },
  {
    value: "text_links",
    label: "Со ссылками",
    icon: "link",
    desc: "Список со ссылками",
  },
  { value: "markdown", label: "Markdown", icon: "edit", desc: "Формат .md" },
  { value: "json", label: "JSON", icon: "code", desc: "Структурированный JSON" },
  { value: "csv", label: "CSV", icon: "chart", desc: "Таблица для Excel" },
];

const privacyIcon = computed(() => {
  if (currentVisibility.value === "private") return "lock";
  if (currentVisibility.value === "link") return "link";
  return "globe";
});

const sortedItems = computed(() => {
  return [...items.value].sort(
    (a, b) => (a.position ?? 0) - (b.position ?? 0),
  );
});

const totalItemsPages = computed(() => Math.max(1, Math.ceil(itemsTotal.value / ITEMS_PER_PAGE)));

watch(itemsPage, () => {
  loadItems();
});

const coverItems = computed(() => {
  return sortedItems.value.slice(0, 3);
});

const currentVisibility = computed((): PlaylistVisibility => {
  if (!playlist.value) return "public";
  return (
    playlist.value.visibility ||
    (playlist.value.is_public ? "public" : "private")
  );
});

const privacyLabel = computed(() => {
  if (currentVisibility.value === "private") return "Приватный";
  if (currentVisibility.value === "link") return "По ссылке";
  return "Публичный";
});

const exportPreview = computed(() => {
  if (!playlist.value) return "";
  const items = exportItems.value.length
    ? [...exportItems.value].sort((a, b) => (a.position ?? 0) - (b.position ?? 0))
    : sortedItems.value;
  const title = playlist.value.title;
  const author = playlist.value.user_username;

  if (exportFormat.value === "text") {
    return (
      `Плейлист: ${title}\nАвтор: @${author}\nАниме: ${items.length}\n\n` +
      items
        .map(
          (item, i) =>
            `${i + 1}. ${item.anime_title}${item.notes ? `\n   ${item.notes}` : ""}`,
        )
        .join("\n")
    );
  }
  if (exportFormat.value === "text_links") {
    return (
      `Плейлист: ${title}\nАвтор: @${author}\n\n` +
      items
        .map((item, i) => {
          const animeUrl = `${window.location.origin}/anime/${item.anime_slug || item.anime}`;
          let str = `${i + 1}. ${item.anime_title}\n   ${animeUrl}`;
          if (item.source_url) str += `\n   Источник: ${item.source_url}`;
          if (item.notes) str += `\n   Заметка: ${item.notes}`;
          return str;
        })
        .join("\n\n")
    );
  }
  if (exportFormat.value === "markdown") {
    return (
      `# ${title}\n> Автор: @${author} · ${items.length} аниме\n\n` +
      items
        .map((item, i) => {
          const animeUrl = `${window.location.origin}/anime/${item.anime_slug || item.anime}`;
          let str = `${i + 1}. [${item.anime_title}](${animeUrl})`;
          if (item.anime_year || item.anime_score)
      str += ` *(${[item.anime_year, item.anime_score ? `рейтинг ${item.anime_score.toFixed(1)}` : ""].filter(Boolean).join(", ")})*`;
          if (item.notes) str += `\n   > ${item.notes}`;
          return str;
        })
        .join("\n")
    );
  }
  if (exportFormat.value === "json") {
    return JSON.stringify(
      {
        title,
        author,
        url: window.location.href,
        exported_at: new Date().toISOString(),
        items: items.map((item, i) => ({
          position: i + 1,
          title: item.anime_title,
          year: item.anime_year || null,
          score: item.anime_score || null,
          url: `${window.location.origin}/anime/${item.anime_slug || item.anime}`,
          source_url: item.source_url || null,
          notes: item.notes || null,
        })),
      },
      null,
      2,
    );
  }
  if (exportFormat.value === "csv") {
    const header = "№,Название,Год,Рейтинг,Ссылка на аниме,Источник,Заметка";
    const rows = items.map((item, i) =>
      [
        i + 1,
        `"${item.anime_title.replace(/"/g, '""')}"`,
        item.anime_year || "",
        item.anime_score ? item.anime_score.toFixed(1) : "",
        `"${window.location.origin}/anime/${item.anime_slug || item.anime}"`,
        `"${(item.source_url || "").replace(/"/g, '""')}"`,
        `"${(item.notes || "").replace(/"/g, '""')}"`,
      ].join(","),
    );
    return [header, ...rows].join("\n");
  }
  return "";
});

const loadPlaylist = async () => {
  const id = route.params.id;
  if (!id) return;
  loading.value = true;
  authorAvatarFailed.value = false;
  try {
    await read(['playlist', id], async () => (await playlistsApi.getPlaylist(id as string)).data, data => {
      playlist.value = data; items.value = data.items || []; itemsTotal.value = data.items_count || 0;
    });
    await loadItems();
  } catch {
    playlist.value = null;
  } finally {
    loading.value = false;
  }
};

const onSortChange = () => {
  itemsPage.value = 1;
  loadItems();
};

const loadItems = async () => {
  if (!playlist.value) return;
  itemsLoading.value = true;
  try {
    const id = playlist.value.id;
    const params = { page: itemsPage.value, page_size: ITEMS_PER_PAGE, ordering: itemsSort.value };
    await read(['playlist-items', id, params], async () => (await playlistsApi.getPlaylistItems(id, params)).data, data => {
      items.value = data.results || []; itemsTotal.value = data.count || 0;
    });
  } catch {
  } finally {
    itemsLoading.value = false;
  }
};

const openEditPage = () => {
  if (!playlist.value) return;
  router.push(`/playlists/${playlist.value.id}/edit`);
};

const watchPlaylist = () => {
  const first = sortedItems.value[0];
  if (!playlist.value || !first) return;
  const target = first.anime_slug || first.anime_id || (typeof first.anime === 'number' ? first.anime : null);
  if (!target) return;
  router.push({
    name: 'anime-watch',
    params: { slug: String(target) },
    query: { playlist: String(playlist.value.id), episode: String(first.episode_number || 1) },
  });
};

const formatDate = (dateStr?: string) => {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
};

const goToAuthor = () => {
  const nickname = String(playlist.value?.user_username || "").replace(/^@+/, "").trim();
  if (nickname) router.push(`/profile/@${encodeURIComponent(nickname)}`);
};

const toggleFavorite = async () => {
  if (!playlist.value) return;
  try {
    if (playlist.value.is_favorited) {
      await playlistsApi.removePlaylistFromFavorites(playlist.value.id);
      playlist.value.is_favorited = false;
      playlist.value.favorites_count = Math.max(
        0,
        playlist.value.favorites_count - 1,
      );
    showToast("Убрано из избранного");
  } else {
    await playlistsApi.addPlaylistToFavorites(playlist.value.id);
    playlist.value.is_favorited = true;
    playlist.value.favorites_count++;
    showToast("Добавлено в избранное");
  }
} catch (err: unknown) {
  console.error(err);
}
};

const sharePlaylist = async () => {
  try {
    if (currentVisibility.value === "link") {
      const res = await playlistsApi.generateShareLink(playlist.value!.id);
      const url = `${window.location.origin}/playlist/shared/${res.data.token}`;
      await navigator.clipboard.writeText(url);
      showToast("Ссылка по токену скопирована!");
    } else {
      await navigator.clipboard.writeText(window.location.href);
      showToast("Ссылка скопирована!");
    }
  } catch {
    navigator.clipboard.writeText(window.location.href);
    showToast("Ссылка скопирована!");
  }
};

const openExportModal = async (initialFormat?: typeof exportFormat.value) => {
  if (!playlist.value) return;
  if (initialFormat) exportFormat.value = initialFormat;
  exportItems.value = [];
  showExportModal.value = true;
  try {
    const all: PlaylistItem[] = [];
    let page = 1;
    let total = playlist.value.items_count || itemsTotal.value;
    do {
      const response = await playlistsApi.getPlaylistItems(playlist.value.id, {
        page,
        page_size: 200,
        ordering: "position",
      });
      const batch = response.data?.results || [];
      all.push(...batch);
      total = response.data?.count ?? total;
      if (!batch.length) break;
      page += 1;
    } while (all.length < total);
    exportItems.value = all;
  } catch {
    exportItems.value = [...sortedItems.value];
  }
};

const copyAllLinks = () => openExportModal("text_links");

const copyAnimeLink = async (item: PlaylistItem) => {
  const url =
    item.source_url && item.source_url.trim()
      ? item.source_url.trim()
      : `${window.location.origin}/anime/${item.anime_slug || item.anime}`;
  try {
    await navigator.clipboard.writeText(url);
    showToast("Ссылка скопирована!");
  } catch {
    fallbackCopyText(url);
    showToast("Ссылка скопирована!");
  }
};

const fallbackCopyText = (text: string) => {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  try {
    document.execCommand("copy");
  } catch (e) {
    console.error("Copy failed:", e);
  }
  document.body.removeChild(textarea);
};

const copyExport = async () => {
  try {
    await navigator.clipboard.writeText(exportPreview.value);
  } catch {
    fallbackCopyText(exportPreview.value);
  }
  showToast("Скопировано в буфер обмена!");
};

const downloadExport = () => {
  const ext: Record<string, string> = {
    text: "txt",
    text_links: "txt",
    markdown: "md",
    json: "json",
    csv: "csv",
  };
  const mime: Record<string, string> = {
    text: "text/plain",
    text_links: "text/plain",
    markdown: "text/markdown",
    json: "application/json",
    csv: "text/csv",
  };
  const safeName = (playlist.value?.title || "playlist")
    .replace(/[^a-zA-Zа-яА-Я0-9]/g, "_")
    .slice(0, 50);
  const filename = `${safeName}.${ext[exportFormat.value]}`;
  const blob = new Blob([exportPreview.value], {
    type: mime[exportFormat.value] + ";charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
  showToast(`Файл ${filename} скачан`);
};

const debouncedAnimeSearch = () => {
  if (searchTimer) clearTimeout(searchTimer);
  if (addAnimeSearch.value.length < 2) {
    animeSearchResults.value = [];
    return;
  }
  searchTimer = setTimeout(async () => {
    animeSearchLoading.value = true;
    try {
      const res = await apiClient.get("/anime/", {
        params: { search: addAnimeSearch.value, page_size: 12 },
      });
      animeSearchResults.value = res.data.results || res.data || [];
    } catch (e) {
      console.error("Search error:", e);
      animeSearchResults.value = [];
    } finally {
      animeSearchLoading.value = false;
    }
  }, TIMING.DEBOUNCE_SHORT);
};

const isAnimeInPlaylist = (animeId: number) => {
  if (!playlist.value?.items) return false;
  return playlist.value.items.some(
    (i) => i.anime === animeId || i.anime_id === animeId,
  );
};

const addAnimeToPlaylist = async (anime: Anime) => {
  if (!playlist.value || isAnimeInPlaylist(anime.id)) return;
  try {
    await playlistsApi.addItemToPlaylist(playlist.value.id, {
      anime: anime.id,
    });
    await loadPlaylist();
    showToast(`«${anime.title_ru || anime.title_en}» добавлено!`);
  } catch (err) {
    const axiosError = err as AxiosError;
    showToast(
      (axiosError.response?.data as { error?: string } | undefined)?.error ||
        "Ошибка добавления",
    );
  }
};

const openRemoveItem = (item: PlaylistItem) => {
  removingItem.value = item;
};

const confirmRemoveItem = async () => {
  if (!playlist.value || !removingItem.value) return;
  try {
    await playlistsApi.removeFromPlaylist(
      playlist.value.id,
      removingItem.value.id,
    );
    await loadPlaylist();
    showToast("Аниме удалено из плейлиста");
    removingItem.value = null;
  } catch {}
};

const openEditItem = (item: PlaylistItem) => {
  editingItem.value = item;
  editItemNotes.value = item.notes || "";
};

const saveItemNotes = async () => {
  if (!playlist.value || !editingItem.value) return;
  itemSaving.value = true;
  try {
    await playlistsApi.updatePlaylistItemNotes(
      playlist.value.id,
      editingItem.value.id,
      editItemNotes.value,
    );
    editingItem.value.notes = editItemNotes.value;
    editingItem.value = null;
    showToast("Заметка сохранена");
  } catch {
  } finally {
    itemSaving.value = false;
  }
};

const confirmDeletePlaylist = async () => {
  if (!playlist.value) return;
  isDeleting.value = true;
  try {
    await playlistsApi.deletePlaylist(playlist.value.id);
    router.push("/playlists");
  } catch (err: unknown) {
    console.error(err);
  } finally {
    isDeleting.value = false;
  }
};

const showToast = (msg: string) => {
  toastMsg.value = msg;
  setTimeout(() => {
    toastMsg.value = "";
  }, 3000);
};

onMounted(async () => {
  if (authStore.user) currentUserId.value = authStore.user.id;
  await loadPlaylist();
});

onUnmounted(() => {
  document.removeEventListener("mousemove", onDragMove);
  document.removeEventListener("mouseup", onDragEnd);
  document.removeEventListener("touchmove", onDragMoveTouch);
  document.removeEventListener("touchend", onDragEnd);
  dragState.insertIndex = null;
});
</script>

<style scoped>
.playlist-detail-page {
  padding: 1.5rem;
  max-width: 960px;
  margin: 0 auto;
  min-height: 100vh;
}

/* ── Загрузка ── */
.detail-loading {
  display: flex;
  gap: 2rem;
  padding: 2rem 0;
}
.loading-cover-skeleton {
  width: 260px;
  flex-shrink: 0;
  aspect-ratio: 1;
  background: var(--surface-4);
  border-radius: var(--radius-lg);
  animation: shimmer 1.5s infinite;
}
.loading-info-skeleton {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-top: 0.5rem;
}
.sk-line {
  height: 13px;
  background: var(--surface-4);
  border-radius: 6px;
  animation: shimmer 1.5s infinite;
}
.w-60 {
  width: 60%;
}
.w-40 {
  width: 40%;
}
.w-80 {
  width: 80%;
}
.sk-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
.sk-btn {
  width: 110px;
  max-width: 100%;
  flex: 0 1 110px;
  height: 38px;
  background: var(--surface-4);
  border-radius: 0.5rem;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.45;
  }
}

/* ── Не найден ── */
.not-found {
  text-align: center;
  padding: 6rem 2rem;
}
.not-found-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}
.not-found h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.5rem;
}
.not-found p {
  color: var(--text-secondary);
  margin: 0 0 1.5rem;
}
.btn-back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
}

/* ── Breadcrumb ── */
.breadcrumb {
  margin-bottom: 1.25rem;
}
.breadcrumb-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
  text-decoration: none;
  transition: color 0.2s;
}
.breadcrumb-link:hover {
  color: var(--accent);
}

/* ── Hero ── */
.playlist-hero {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.75rem;
  align-items: flex-start;
}
.hero-cover {
  aspect-ratio: 2 / 3;
  border-radius: var(--radius-lg);
  overflow: hidden;
  width: 240px;
  flex-shrink: 0;
  position: relative;
}
.cover-mosaic {
  width: 100%;
  aspect-ratio: 1;
  display: grid;
  gap: 3px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-4);
}
/* 1 элемент - на всю ширину */
.cover-mosaic.items-1 {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
}
/* 2 элемента - горизонтально */
.cover-mosaic.items-2 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr;
}
/* 3 элемента - первый большой, два маленьких справа */
.cover-mosaic.items-3 {
  grid-template-columns: 2fr 1fr;
  grid-template-rows: 1fr 1fr;
}
.cover-mosaic.items-3 .mosaic-cell:first-child {
  grid-row: span 2;
}
.mosaic-cell {
  position: relative;
  background: var(--surface-4);
  overflow: hidden;
}
.mosaic-cell img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}
.playlist-hero:hover .mosaic-cell img {
  transform: scale(1.05);
}
.mosaic-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}
.mosaic-extra {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 999px;
  backdrop-filter: blur(4px);
}
.privacy-hero-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  backdrop-filter: blur(6px);
}
.privacy-public {
  background: rgba(34, 197, 94, 0.85);
  color: #fff;
}
.privacy-private {
  background: rgba(239, 68, 68, 0.85);
  color: #fff;
}
.privacy-link {
  background: rgba(58, 134, 255, 0.85);
  color: #fff;
}

.hero-info {
  flex: 1;
}
.hero-title {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 0.75rem;
  line-height: 1.3;
}
.hero-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.1rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
}
.author-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
  transition: color 0.2s;
}
.author-chip:hover {
  color: var(--accent);
}
.author-chip-avatar {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  object-fit: cover;
}
.author-chip-avatar-ph {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.58rem;
  font-weight: 700;
}
.meta-dot {
  color: var(--border-strong);
}
.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.875rem;
}
.action-hero-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.55rem 0.9rem;
  background: var(--surface-4);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-lg);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.18s;
  white-space: nowrap;
}
.action-hero-btn:hover {
  background: var(--surface-3);
  border-color: var(--accent);
  color: var(--accent);
}
.action-hero-btn:disabled { opacity: .45; cursor: not-allowed; transform: none; }
.action-hero-btn.active {
  background: var(--surface-4);
  border-color: var(--accent-hover);
  color: var(--accent);
}
.action-hero-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.action-hero-btn.primary:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  color: #fff;
}
.action-hero-btn.danger:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #ef4444;
}
.action-hero-btn.wheel {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: #fff;
}
.action-hero-btn.wheel:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.hero-stats {
  display: flex;
  gap: 0.75rem;
}
.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

/* ── Описание ── */
.description-section {
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-lg);
  padding: 1.1rem 1.25rem;
  margin-bottom: 1.5rem;
}
.section-label {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}
.description-text {
  font-size: 0.9375rem;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0;
  white-space: pre-wrap;
}

/* ── Список аниме ── */
.anime-section {
  margin-bottom: 2rem;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}
.drag-hint {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.anime-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sort-select-sm {
  padding: 0.35rem 0.6rem;
  background: var(--surface-4);
  border: 1px solid var(--border-strong);
  border-radius: 0.375rem;
  color: var(--text-secondary);
  font-size: 0.75rem;
  cursor: pointer;
}

.items-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 1rem;
}

.page-indicator {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  font-weight: 600;
}

.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.anime-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-tertiary);
  background: var(--surface-3);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
.btn-add-empty {
  padding: 0.6rem 1.25rem;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.anime-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
  position: relative;
}

.drag-placeholder {
  background: var(--surface-4);
  border: 2px dashed var(--accent);
  border-radius: 0.625rem;
  opacity: 0.7;
  box-shadow: 0 0 16px rgba(58, 134, 255, 0.35);
}

.anime-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 0.625rem;
  transition:
    border-color 0.15s,
    background 0.15s,
    box-shadow 0.2s,
    transform 0.15s;
  position: relative;
}
.anime-row:hover {
  border-color: var(--accent);
  background: var(--surface-4);
}
.anime-row.is-dragging {
  background: var(--surface-4);
  border-color: var(--accent);
  cursor: grabbing !important;
  z-index: 100;
}
.anime-row.is-being-dragged {
  cursor: grabbing !important;
  opacity: 0.5;
}
.anime-row.drag-above {
  background: rgba(58, 134, 255, 0.06);
}
.anime-row.drag-below {
  background: rgba(58, 134, 255, 0.06);
}

/* Для мобильных - более долгие и заметные индикаторы */
@media (pointer: coarse) {
  .anime-row.drag-above {
    border-top-width: 3px;
  }
  .anime-row.drag-below {
    border-bottom-width: 4px !important;
  }
  .anime-row.insertion-point::after {
    height: 6px;
  }
  .row-index-wrap.is-handle {
    /* Разрешаем скролл страницы, только touch на handle блокирует */
  }
  .drag-handle {
    min-width: 44px; /* Увеличенная зона для touch */
    min-height: 44px;
  }
}

/* Drag handle */
.row-index-wrap {
  width: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.row-index-wrap.is-handle {
  cursor: grab;
}
.row-index-wrap.is-handle:active {
  cursor: grabbing;
}
.row-index {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-tertiary);
}
.drag-handle {
  width: 32px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  border-radius: 6px;
  transition: all 0.15s;
  flex-shrink: 0;
  touch-action: none; /* Для drag handle только */
}
.drag-handle:hover {
  color: var(--accent);
  background: rgba(58, 134, 255, 0.1);
}
.drag-handle:active {
  cursor: grabbing;
  transform: scale(1.1);
}

/* Постер */
.row-poster-link {
  flex-shrink: 0;
}
.row-poster {
  width: 44px;
  height: 62px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--surface-4);
  flex-shrink: 0;
}
.row-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.row-poster-ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

/* Инфо */
.row-info {
  flex: 1;
  min-width: 0;
}
.row-title {
  display: block;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.15s;
  margin-bottom: 0.15rem;
}
.row-title:hover {
  color: var(--accent);
}
.row-note {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.78rem;
  color: var(--text-secondary);
  margin-bottom: 0.15rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.row-meta {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-wrap: wrap;
}
.row-meta-chip {
  font-size: 0.7rem;
  padding: 1px 5px;
  background: var(--surface-4);
  border-radius: 4px;
  color: var(--text-tertiary);
  font-weight: 600;
}

.row-progress {
  position: relative;
  width: 100%;
  height: 8px;
  background: var(--surface-4);
  border: 1px solid var(--border-strong);
  border-radius: 4px;
  overflow: hidden;
  margin-top: 0.25rem;
  box-sizing: border-box;
}
.row-progress.is-empty {
  opacity: 0.5;
}

.row-progress-bar {
  position: absolute;
  inset: 0 auto 0 0;
  height: 100%;
  background: var(--accent);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.row-progress.is-empty .row-progress-bar {
  background: var(--border-subtle);
}

.row-progress-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 4px;
  font-size: 0.55rem;
  font-weight: 700;
  color: var(--text-primary);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
  pointer-events: none;
}

/* Действия строки */
.row-actions {
  display: flex;
  align-items: center;
  gap: 1px;
  flex-shrink: 0;
}
.row-action-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 0.375rem;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
}
.row-action-btn:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}
.row-action-btn.play:hover {
  background: rgba(58, 134, 255, 0.12);
  color: var(--accent);
}
.row-action-btn.danger:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* ── Модалки ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}
.modal-box {
  background: var(--surface-3);
  border-radius: 1rem;
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.5);
}
.modal-box-sm {
  max-width: 400px;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.1rem 1.4rem;
  border-bottom: 1px solid var(--border-subtle);
}
.modal-header h3 {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.modal-close-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.modal-close-btn:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}
.modal-body {
  padding: 1.1rem 1.4rem;
  overflow-y: auto;
  flex: 1;
}
.modal-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  padding: 1.1rem 1.4rem;
  border-top: 1px solid var(--border-subtle);
}

.btn-modal-cancel {
  flex: 1 1 100px;
  min-width: 0;
  padding: 0.7rem;
  background: transparent;
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.btn-modal-cancel:hover {
  background: var(--surface-4);
}
.btn-modal-save {
  flex: 2 1 140px;
  min-width: 0;
  padding: 0.7rem;
  background: var(--accent);
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: #fff;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
}
.btn-modal-save:hover:not(:disabled) {
  background: var(--accent-hover);
}
.btn-modal-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-modal-save.outline {
  flex: 1 1 120px;
  background: transparent;
  color: var(--accent);
  border: 1px solid var(--accent);
}
.btn-modal-save.outline:hover {
  background: rgba(58, 134, 255, 0.08);
}
.btn-modal-danger {
  flex: 2 1 140px;
  min-width: 0;
  padding: 0.7rem;
  background: #ef4444;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: #fff;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
}
.btn-modal-danger:hover:not(:disabled) {
  background: #dc2626;
}
.btn-modal-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Поиск в модалке */
.modal-search-wrap {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 0.875rem;
}
.modal-search-icon {
  position: absolute;
  left: 0.75rem;
  color: var(--text-tertiary);
  pointer-events: none;
}
.modal-search-input {
  width: 100%;
  padding: 0.7rem 2.5rem 0.7rem 2.5rem;
  border: 1px solid var(--border-strong);
  border-radius: 0.625rem;
  font-size: 0.9rem;
  color: var(--text-primary);
  background: var(--surface-4);
  outline: none;
  transition: border-color 0.2s;
}
.modal-search-input:focus {
  border-color: var(--accent);
}
.modal-search-clear {
  position: absolute;
  right: 0.6rem;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 50%;
}
.modal-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  justify-content: center;
  padding: 1.5rem;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}
.modal-results {
  display: flex;
  flex-direction: column;
  gap: 1px;
  max-height: 360px;
  overflow-y: auto;
}
.modal-result-item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.55rem 0.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.12s;
}
.modal-result-item:hover:not(.disabled) {
  background: var(--surface-4);
}
.modal-result-item.disabled {
  opacity: 0.55;
  cursor: default;
}
.modal-result-poster {
  width: 36px;
  height: 50px;
  object-fit: cover;
  border-radius: 3px;
  flex-shrink: 0;
}
.modal-result-poster-ph {
  width: 36px;
  height: 50px;
  background: var(--surface-4);
  border-radius: 3px;
  flex-shrink: 0;
}
.modal-result-info {
  flex: 1;
  min-width: 0;
}
.modal-result-title {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.modal-result-meta {
  font-size: 0.72rem;
  color: var(--text-tertiary);
}
.already-added {
  font-size: 0.72rem;
  color: #22c55e;
  font-weight: 600;
  flex-shrink: 0;
}
.btn-add-anime {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  border: none;
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
}
.btn-add-anime:hover {
  background: var(--accent-hover);
  transform: scale(1.1);
}
.modal-empty {
  text-align: center;
  padding: 2rem;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}
.modal-empty-hint {
  text-align: center;
  padding: 2rem;
  color: var(--text-tertiary);
  font-size: 0.875rem;
  opacity: 0.6;
}

/* Confirm модалка */
.confirm-body {
  text-align: center;
  padding: 0.5rem 0;
}
.confirm-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}
.confirm-anime-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding: 0.625rem;
  background: var(--surface-4);
  border-radius: 0.5rem;
}
.confirm-poster {
  width: 36px;
  height: 50px;
  object-fit: cover;
  border-radius: 3px;
}
.confirm-poster-ph {
  width: 36px;
  height: 50px;
  background: var(--surface-3);
  border-radius: 3px;
  flex-shrink: 0;
}
.confirm-anime-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  text-align: left;
}
.confirm-text {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* Формы */
.form-group {
  margin-bottom: 1rem;
}
.form-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.35rem;
}
.req {
  color: #f43f5e;
}
.form-input,
.form-textarea {
  width: 100%;
  padding: 0.7rem;
  font-family: inherit;
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.9rem;
  color: var(--text-primary);
  background: var(--surface-3);
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.form-input:focus,
.form-textarea:focus {
  border-color: var(--accent);
}
.form-textarea {
  resize: vertical;
  min-height: 76px;
}
.privacy-chips {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}
.privacy-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 0.9rem;
  background: var(--surface-4);
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.15s;
}
.privacy-chip.active {
  background: rgba(58, 134, 255, 0.12);
  border-color: var(--accent);
  color: var(--accent);
}
.visibility-hint {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  margin: 0.5rem 0 0;
}

/* Редактирование заметки */
.anime-edit-preview {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem;
  background: var(--surface-4);
  border-radius: 0.5rem;
  margin-bottom: 0.875rem;
}
.edit-preview-poster {
  width: 38px;
  height: 54px;
  object-fit: cover;
  border-radius: 3px;
}
.edit-preview-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
}

/* Экспорт */
.export-formats {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.export-fmt {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.875rem;
  background: var(--surface-4);
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.15s;
}
.export-fmt.active {
  background: rgba(58, 134, 255, 0.08);
  border-color: var(--accent);
}
.fmt-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}
.fmt-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}
.fmt-desc {
  font-size: 0.72rem;
  color: var(--text-tertiary);
}
.export-preview {
  background: var(--surface-4);
  border-radius: 0.5rem;
  padding: 0.75rem;
  max-height: 200px;
  overflow-y: auto;
}
.export-text {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-secondary);
  white-space: pre-wrap;
  font-family: "Courier New", monospace;
  line-height: 1.5;
}

/* Spinner */
.spinner-sm {
  width: 15px;
  height: 15px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.spinner-sm-dark {
  width: 15px;
  height: 15px;
  border: 2px solid var(--border-subtle);
  border-top-color: #ef4444;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Toast */
.toast-notification {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.7rem 1.1rem;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 2rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  z-index: 9999;
  white-space: nowrap;
}
.toast-notification svg {
  color: #22c55e;
}
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(16px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(8px);
}

/* Модал анимации */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.22s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-box,
.modal-leave-to .modal-box {
  transform: scale(0.96) translateY(12px);
}

/* Responsive */
@media (max-width: 1024px) {
  .detail-loading {
    flex-direction: column;
  }

  .loading-cover-skeleton {
    width: min(260px, 100%);
  }
}

@media (max-width: 767px) {
  .anime-row { flex-wrap: wrap; }
  .row-info { min-width: 0; }
  .row-actions { width: 100%; justify-content: flex-end; flex-wrap: wrap; }
  .playlist-detail-page {
    padding: 1rem;
  }
  .playlist-hero {
    flex-direction: column;
  }
  .hero-cover {
    width: 100%;
    max-width: 280px;
  }
  .hero-title {
    font-size: 1.3rem;
  }
  .hero-actions {
    gap: 0.3rem;
  }
  .action-hero-btn {
    padding: 0.5rem 0.7rem;
    font-size: 0.75rem;
  }
  .row-actions {
    gap: 0;
  }
}
</style>
