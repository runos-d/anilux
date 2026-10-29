<template>
  <div class="feed-page">
    <div class="container">
      <!-- Page Header -->
      <header class="page-header">
        <!-- <div class="page-header-text">
          <h1 class="page-title">Лента</h1>
          <p class="page-subtitle">Посты, обновления и события вашего сообщества</p>
        </div> -->
        <!-- <button @click="openCreatePostModal()" class="btn-create-post">
          <SakuraIcon name="plus" :size="16" />
          <span>Создать пост</span>
        </button> -->
      </header>

      <!-- Feed Tabs -->
      <div class="feed-tabs">
        <button
          v-for="tab in feedTabs"
          :key="tab.id"
          @click="switchTab(tab.id)"
          :class="['tab-btn', { active: activeTab === tab.id }]"
        >
          <SakuraIcon v-if="tab.icon" :name="tab.icon" :size="16" />
          <span>{{ tab.label }}</span>
          <span v-if="tab.id === 'feed' && newPostsCount > 0" class="new-posts-badge">
            {{ newPostsCount }}
          </span>
        </button>
      </div>

      <!-- Filters and Sort Bar (only for Feed tab) -->
      <div v-if="activeTab === 'feed'" class="filters-bar">
        <div class="filters-section">
          <button @click="showFilters = !showFilters" class="filter-toggle">
            <SakuraIcon name="filter" :size="14" />
            <span>Фильтры</span>
            <SakuraIcon
              name="arrow-down"
              :size="14"
              class="arrow"
              :class="{ open: showFilters }"
            />
          </button>

          <div class="tag-filter-inline">
            <div class="tag-input-wrapper">
              <SakuraIcon name="hash" :size="14" class="tag-icon" />
              <input
                v-model="tagInput"
                @keydown.enter="addTag"
                @keydown.backspace="handleTagBackspace"
                @blur="addTag"
                placeholder="Теги"
                class="tag-input"
              />
              <button v-if="filters.tags.length > 0" @click="clearAllTags" class="tag-clear-all" title="Очистить теги">
                <SakuraIcon name="x" :size="14" />
              </button>
            </div>
          </div>

          <!-- Collapsible Filters -->
          <div v-if="showFilters" class="filters-dropdown">
            <div class="filter-group">
              <label class="filter-label">Тип контента:</label>
              <div class="toggle-buttons">
                <button
                  :class="['toggle-btn', { active: filters.myPosts }]"
                  @click="toggleFilter('myPosts')"
                >
                  <SakuraIcon name="user" :size="14" />
                  <span>Мои посты</span>
                </button>
                <button
                  :class="['toggle-btn', { active: filters.subscriptions }]"
                  @click="toggleFilter('subscriptions')"
                >
                  <SakuraIcon name="subscriptions" :size="14" />
                  <span>Подписки</span>
                </button>
                <button
                  :class="['toggle-btn', { active: filters.withAnime }]"
                  @click="toggleFilter('withAnime')"
                >
                  <SakuraIcon name="anime-tv" :size="14" />
                  <span>С аниме</span>
                </button>
              </div>
            </div>

            <div class="filter-group">
              <label class="filter-label">За период:</label>
              <div class="period-buttons">
                <button
                  :class="['period-btn', { active: filters.period === 'all' }]"
                  @click="filters.period = 'all'; applyFilters()"
                >
                  Всё время
                </button>
                <button
                  :class="['period-btn', { active: filters.period === 'day' }]"
                  @click="filters.period = 'day'; applyFilters()"
                >
                  День
                </button>
                <button
                  :class="['period-btn', { active: filters.period === 'week' }]"
                  @click="filters.period = 'week'; applyFilters()"
                >
                  Неделя
                </button>
                <button
                  :class="['period-btn', { active: filters.period === 'month' }]"
                  @click="filters.period = 'month'; applyFilters()"
                >
                  Месяц
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="sort-section">
          <span class="sort-section-label">Сортировка</span>
          <select v-model="filters.sort" @change="applyFilters" class="sort-select">
            <option value="new">Новые</option>
            <option value="old">Старые</option>
            <option value="best">Лучшие</option>
            <option value="discussed">Обсуждаемые</option>
          </select>
        </div>
      </div>

      <!-- Active Filters Tags -->
      <div v-if="activeTab === 'feed' && activeFilterTags.length > 0" class="active-filters">
        <span
          v-for="tag in activeFilterTags"
          :key="tag.key"
          class="filter-tag"
          @click="removeFilter(tag.key)"
        >
          {{ tag.label }}
          <SakuraIcon name="x" :size="12" />
        </span>
        <button class="clear-all" @click="clearAllFilters">Очистить всё</button>
      </div>

      <div class="feed-layout">
        <!-- Main Content Area -->
        <main class="feed-main">
          <!-- SUBSCRIPTIONS TAB - Shows profile cards with sub-tabs -->
          <div v-if="activeTab === 'subscriptions'" class="subscriptions-tab">
            <!-- Sub-tabs -->
            <div class="sub-tabs">
              <button
                :class="['sub-tab-btn', { active: subscriptionsSubTab === 'profiles' }]"
                @click="subscriptionsSubTab = 'profiles'"
              >
                <SakuraIcon name="user" /> Профили
              </button>
              <button
                :class="['sub-tab-btn', { active: subscriptionsSubTab === 'favorites' }]"
                @click="subscriptionsSubTab = 'favorites'; loadFavoritePosts()"
              >
                <SakuraIcon name="star" /> Избранные посты
              </button>
            </div>

            <!-- Profiles Sub-tab -->
            <div v-if="subscriptionsSubTab === 'profiles'">
              <div class="tab-header">
                <input
                  v-model="subscriptionsSearch"
                  placeholder="Поиск подписок..."
                  class="search-input"
                  @input="debouncedSearchSubscriptions"
                >
                <!-- <select v-model="subscriptionsSort" @change="loadSubscriptions" class="sort-select">
                  <option value="date">По дате</option>
                  <option value="name">По имени</option>
                  <option value="activity">По активности</option>
                </select> -->
              </div>

              <div v-if="loadingSubscriptions" class="loading-state">
                <div class="skeleton-user" v-for="i in 5" :key="i">
                  <div class="skeleton-avatar"></div>
                  <div class="skeleton-info">
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line short"></div>
                  </div>
                </div>
              </div>

              <div v-else-if="subscriptions.length === 0" class="empty-state">
                <div class="empty-icon"> <SakuraIcon name="users" :size="56" /> </div>
                <h3>Нет подписок</h3>
                <p>Подпишитесь на интересных авторов!</p>
              </div>

              <div v-else class="subscriptions-grid">
                <div v-for="user in subscriptions" :key="user.id" class="subscription-card clickable" @click="goToProfile(user.id)">
                  <img :src="user.avatar_url || user.avatar || defaultAvatar" class="avatar-lg" alt="">
                  <div class="user-info">
                    <h4>{{ user.display_name || user.username }}</h4>
                    <span class="username">@{{ user.username }}</span>
                    <span class="followers">{{ user.followers_count || 0 }} подписчиков</span>
                  </div>
                  <div class="user-actions" @click.stop>
                    <button class="btn-following" @click="unfollowUser(user.id)">
                      <SakuraIcon name="check" :size="14" /> Подписан
                    </button>
                    <button class="btn-message" @click="openChat(user.id)"> <SakuraIcon name="message" /> </button>
                  </div>
                </div>
              </div>

              <div v-if="hasMoreSubscriptions" class="load-more">
                <button @click="loadMoreSubscriptions" :disabled="loadingMoreSubscriptions" class="btn-load-more">
                  {{ loadingMoreSubscriptions ? 'Загрузка...' : 'Загрузить ещё' }}
                </button>
              </div>
            </div>

            <!-- Favorites Posts Sub-tab -->
            <div v-else-if="subscriptionsSubTab === 'favorites'">
              <div v-if="loadingFavoritePosts" class="loading-state">
                <div class="skeleton-post" v-for="i in 3" :key="i">
                  <div class="skeleton-header">
                    <div class="skeleton-avatar"></div>
                    <div class="skeleton-info">
                      <div class="skeleton-line short"></div>
                      <div class="skeleton-line"></div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else-if="favoritePosts.length === 0" class="empty-state">
                <div class="empty-icon"> <SakuraIcon name="star" :size="56" /> </div>
                <h3>Нет избранных постов</h3>
                <p>Добавляйте посты в избранное, чтобы они появились здесь</p>
              </div>

              <div v-else class="posts-list">
                <PostCard
                  v-for="post in favoritePosts"
                  :key="post.id"
                  :post="post"
                  @like="handleLike"
                  @dislike="handleDislike"
                  @bookmark="toggleBookmark"
                  @menu="openPostMenu"
                />
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'bookmarks'" class="bookmarks-tab">
            <div class="tab-header">
              <input
                v-model="bookmarkSearch"
                placeholder="Поиск в сохранённых..."
                class="search-input"
              >
            </div>
            <div v-if="loadingBookmarks" class="loading-state">
              <div class="skeleton-post" v-for="i in 4" :key="i">
                <div class="skeleton-header">
                  <div class="skeleton-avatar"></div>
                  <div class="skeleton-info">
                    <div class="skeleton-line short"></div>
                    <div class="skeleton-line"></div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="filteredBookmarks.length === 0" class="empty-state">
              <div class="empty-icon"> <SakuraIcon name="star" :size="56" /> </div>
              <h3>Нет избранных постов</h3>
              <p>Добавляйте посты в избранное, чтобы они появились здесь</p>
            </div>
            <div v-else class="posts-list">
              <PostCard
                v-for="post in filteredBookmarks"
                :key="post.id"
                :post="post"
                @like="handleLike"
                @dislike="handleDislike"
                @bookmark="toggleBookmark"
                @menu="openPostMenu"
                @comment="openComments"
              />
            </div>
          </div>

          <div v-else-if="activeTab === 'pinned'" class="pinned-tab">
            <div v-if="loadingPinned" class="loading-state">
              <div class="skeleton-post" v-for="i in 3" :key="i">
                <div class="skeleton-header">
                  <div class="skeleton-avatar"></div>
                  <div class="skeleton-info">
                    <div class="skeleton-line short"></div>
                    <div class="skeleton-line"></div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="pinnedPosts.length === 0" class="empty-state">
              <div class="empty-icon"> <SakuraIcon name="pin" :size="56" /> </div>
              <h3>Нет закреплённых постов</h3>
              <p>Закрепляйте посты через меню поста, чтобы они появились здесь</p>
            </div>
            <div v-else class="posts-list">
              <div v-for="post in pinnedPosts" :key="post.id" class="pinned-post-wrapper">
                <PostCard
                  :post="post"
                  @like="handleLike"
                  @dislike="handleDislike"
                  @bookmark="toggleBookmark"
                  @menu="openPostMenu"
                  @comment="openComments"
                />
                <button class="btn-unpin" @click="unpinPostFromTab(post)"><SakuraIcon name="pin" /> Открепить</button>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'not_interested'" class="not-interested-tab">
            <div class="sub-tabs">
              <button
                :class="['sub-tab-btn', { active: notInterestedSubTab === 'profiles' }]"
                @click="notInterestedSubTab = 'profiles'"
              >
                <SakuraIcon name="user" /> Скрытые профили
              </button>
              <button
                :class="['sub-tab-btn', { active: notInterestedSubTab === 'posts' }]"
                @click="notInterestedSubTab = 'posts'; loadHiddenPosts()"
              >
                <SakuraIcon name="file-text" /> Скрытые посты
              </button>
            </div>

            <div v-if="notInterestedSubTab === 'profiles'">
              <div class="tab-header">
                <input
                  v-model="notInterestedSearch"
                  placeholder="Поиск скрытых..."
                  class="search-input"
                  @input="debouncedSearchNotInterested"
                >
              </div>

              <div v-if="loadingNotInterested" class="loading-state">
                <div class="skeleton-user" v-for="i in 3" :key="i">
                  <div class="skeleton-avatar"></div>
                  <div class="skeleton-info">
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line short"></div>
                  </div>
                </div>
              </div>

              <div v-else-if="notInterestedUsers.length === 0" class="empty-state">
                <div class="empty-icon"> <SakuraIcon name="eye-off" :size="56" /> </div>
                <h3>Нет скрытых профилей</h3>
                <p>Профили, которые вы скроете, появятся здесь</p>
              </div>

              <div v-else class="subscriptions-grid">
                <div v-for="user in notInterestedUsers" :key="user.id" class="subscription-card blocked clickable" @click="goToProfile(user.id)">
                  <img :src="user.avatar_url || user.avatar || defaultAvatar" class="avatar-lg" alt="">
                  <div class="user-info">
                    <h4>{{ user.display_name || user.username }}</h4>
                    <span class="username">@{{ user.username }}</span>
                    <span class="hidden-date"><SakuraIcon name="ban" /> Заблокирован: {{ formatDate(user.hidden_at) }}</span>
                    <span v-if="user.reason" class="reason">{{ user.reason }}</span>
                  </div>
                  <div class="user-actions" @click.stop>
                    <button class="btn-unblock" @click="unhideUser(user.id)">
                      Разблокировать
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="notInterestedSubTab === 'posts'">
              <div v-if="loadingHiddenPosts" class="loading-state">
                <div class="skeleton-post" v-for="i in 3" :key="i">
                  <div class="skeleton-header">
                    <div class="skeleton-avatar"></div>
                    <div class="skeleton-info">
                      <div class="skeleton-line short"></div>
                      <div class="skeleton-line"></div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else-if="hiddenPosts.length === 0" class="empty-state">
                <div class="empty-icon"> <SakuraIcon name="file-text" :size="56" /> </div>
                <h3>Нет скрытых постов</h3>
                <p>Посты, которые вы отметите как "Не интересно", появятся здесь</p>
              </div>

              <div v-else class="posts-list">
                <div v-for="item in hiddenPosts" :key="item.id" class="hidden-post-card">
                  <div class="hidden-post-info" @click="openHiddenPost(item)">
                    <span class="hidden-post-title">{{ item.post_preview || 'Пост #' + item.post_id }}</span>
                    <span class="hidden-date">Скрыт: {{ formatDate(item.hidden_at) }}</span>
                  </div>
                  <button class="btn-restore" @click="restorePost(item.post_id)">
                    Восстановить
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'popular'" class="popular-tab">
            <div class="popular-header">
              <h3 class="popular-title">
                <SakuraIcon name="sparkles" :size="16" />
                Рекомендуемые каналы
              </h3>
              <p class="popular-subtitle">
                Авторы, которые постят то, что вам нравится. Подпишитесь на кого-то нового!
              </p>
            </div>

            <div v-if="loadingPopular" class="loading-state">
              <div class="skeleton-user" v-for="i in 5" :key="i">
                <div class="skeleton-avatar"></div>
                <div class="skeleton-info">
                  <div class="skeleton-line"></div>
                  <div class="skeleton-line short"></div>
                </div>
              </div>
            </div>

            <div v-else-if="popularChannels.length === 0" class="empty-state">
              <div class="empty-icon"> <SakuraIcon name="users" :size="56" /> </div>
              <h3>Пока нет рекомендаций</h3>
              <p>Лайкайте посты и сохраняйте их в избранное, чтобы мы подобрали для вас авторов</p>
            </div>

            <div v-else class="popular-channels-list">
              <div
                v-for="(channel, index) in popularChannels"
                :key="channel.user_id"
                class="popular-channel-item"
                @click="openChannel(channel)"
              >
                <span class="popular-channel-rank">{{ index + 1 }}</span>
                <img
                  :src="channel.avatar || defaultAvatar"
                  :alt="channel.display_name"
                  class="matching-channel-avatar"
                />
                <div class="matching-channel-info">
                  <span class="matching-channel-name">{{ channel.display_name }}</span>
                  <span class="matching-channel-username">@{{ channel.username }}</span>
                  <div class="matching-channel-reasons" v-if="channel.match_reasons.length">
                    <span
                      v-for="reason in channel.match_reasons"
                      :key="reason"
                      class="matching-reason-tag"
                    >
                      {{ reason }}
                    </span>
                  </div>
                </div>
                <div class="matching-channel-stats">
                  <span class="matching-posts-count">
                    {{ channel.posts_count }} постов · {{ channel.followers_count }} подписчиков
                  </span>
                  <button
                    v-if="!channel.is_following"
                    class="matching-follow-btn"
                    @click.stop="followChannel(channel)"
                  >
                    Подписаться
                  </button>
                  <button
                    v-else
                    class="matching-follow-btn following"
                    @click.stop="unfollowChannel(channel)"
                  >
                    Отписаться
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'reports'" class="reports-tab">
            <div class="tab-header">
              <select v-model="reportsFilter.status" @change="loadReports" class="filter-select">
                <option value="">Все статусы</option>
                <option value="pending">Новые</option>
                <option value="in_progress">В процессе</option>
                <option value="resolved">Рассмотренные</option>
              </select>
              <select v-model="reportsFilter.reason" @change="loadReports" class="filter-select">
                <option value="">Все причины</option>
                <option value="copyright">Авторские права</option>
                <option value="inappropriate">Неприемлемый контент</option>
                <option value="spam">Спам</option>
                <option value="harassment">Оскорбления</option>
                <option value="spoiler">Спойлер</option>
                <option value="other">Другое</option>
              </select>
            </div>

            <div v-if="loadingReports" class="loading-state">
              <div class="skeleton-report" v-for="i in 3" :key="i">
                <div class="skeleton-line"></div>
                <div class="skeleton-line medium"></div>
              </div>
            </div>

            <div v-else-if="reports.length === 0" class="empty-state">
              <div class="empty-icon"> <SakuraIcon name="clipboard" :size="56" /> </div>
              <h3>Нет жалоб</h3>
              <p>Нет жалоб для рассмотрения</p>
            </div>

            <div v-else class="reports-list">
              <div v-for="report in reports" :key="report.id" class="report-card">
                <div class="report-header">
                  <span class="report-type">{{ getContentTypeLabel(report.content_type) }}</span>
                  <span :class="['report-status', report.status]">{{ getStatusLabel(report.status) }}</span>
                </div>
                <div class="report-content">
                  <p class="report-reason">{{ getReasonLabel(report.reason) }}</p>
                  <p v-if="report.comment" class="report-description">{{ report.comment }}</p>
                  <div class="report-meta">
                    <span>От: {{ report.reporter?.username || 'Анон' }}</span>
                    <span>Дата: {{ formatDate(report.created_at) }}</span>
                  </div>
                </div>
                <div class="report-actions">
                  <button class="btn-review" @click="openReportDetail(report)">
                    Рассмотреть
                  </button>
                  <button class="btn-reject" @click="rejectReport(report.id)">
                    Отклонить
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="feed-tab">
            <div class="composer-card">
              <img :src="currentUser?.avatar || defaultAvatar" class="composer-avatar" alt="Avatar">
              <div class="composer-body">
                <textarea
                  ref="composerInput"
                  v-model="composerText"
                  class="composer-field"
                  rows="1"
                  placeholder="Что у вас нового?"
                  @input="autoResizeComposer"
                  @keydown.enter.exact.prevent="submitComposerPost"
                >
                </textarea>
                <button
                    class="composer-submit"
                    :disabled="!composerCanSubmit || composerSubmitting"
                    title="Опубликовать"
                    @click="submitComposerPost"
                  >
                  <span>
                    <SakuraIcon v-if="!composerSubmitting" name="send" :size="16" />
                    <span v-else class="dots">...</span>
                  </span>
                </button>
                <div class="composer-hashtag-hint">Теги пишутся через решётку, например: #аниме #ван-пис</div>
                <div class="composer-actions">
                  <!-- <button class="composer-action" :class="{ active: composerExcerpts.length > 0 }" @click="openAttachModal('excerpt')">Отрывки</button> -->
                  <button
                    class="composer-action"
                                        :class="{ active: composerMedia.length > 0 }"
                    title="Фото или видео"
                    @click="openAttachModal('media')"
                  >
                    <SakuraIcon name="image" :size="18" />
                    <span>Фото/Видео</span>
                  </button>
                  <button
                    class="composer-action"
                    :class="{ active: composerAnimes.length > 0 }"
                    title="Прикрепить аниме"
                    @click="openAttachModal('anime')"
                  >
                    <SakuraIcon name="anime-tv" :size="18" />
                    <span>Аниме</span>
                  </button>
                  <button
                    class="composer-action"
                    :class="{ active: composerPlaylists.length > 0 }"
                    title="Прикрепить плейлист"
                    @click="openAttachModal('playlist')"
                  >
                    <SakuraIcon name="list" :size="18" />
                    <span>Плейлист</span>
                  </button>
                  <label class="composer-spoiler-toggle">
                    <span class="toggle-switch" :class="{ active: composerIsSpoiler }">
                      <span class="toggle-slider"></span>
                    </span>
                    <input type="checkbox" v-model="composerIsSpoiler" class="toggle-input" />
                    <span class="toggle-text">Спойлер</span>
                  </label>
                </div>

                <div v-if="composerIsSpoiler" class="composer-spoiler-field">
                  <SakuraIcon name="alert-circle" :size="14" />
                  <input
                    v-model="composerSpoilerFor"
                    type="text"
                    placeholder="О чём спойлер? (например: Конец Наруто)"
                    class="composer-spoiler-input"
                  />
                </div>

                <div
                  v-if="
                    composerAnimes.length > 0 ||
                    composerPlaylists.length > 0 ||
                    composerMedia.length > 0
                  "
                  class="composer-attachments"
                >
                  <div
                    v-for="(a, idx) in composerAnimes"
                    :key="'anime-' + a.id"
                    class="composer-attachment composer-attachment-anime"
                  >
                    <img v-if="getAnimePoster(a)" :src="getAnimePoster(a)" alt="" />
                    <div v-else class="composer-attachment-ph">
                      <SakuraIcon name="anime-tv" :size="18" />
                    </div>
                    <div class="composer-attachment-body">
                      <span class="composer-attachment-title">{{ a.title_ru || a.title_en }}</span>
                      <div class="composer-attachment-rating">
                        <span>Оценка</span>
                        <input
                          type="number"
                          v-model.number="composerAnimeRatings[idx]"
                          min="0"
                          max="10"
                          placeholder="-"
                          @blur="clampRating(idx)"
                        />
                      </div>
                    </div>
                    <button class="composer-attachment-remove" @click="removeComposerAnime(idx)" aria-label="Удалить"><SakuraIcon name="x" :size="16" /></button>
                  </div>
                  <div
                    v-for="(p, idx) in composerPlaylists"
                    :key="'playlist-' + p.id"
                    class="composer-attachment composer-attachment-anime"
                  >
                    <img v-if="getPlaylistPoster(p)" :src="getPlaylistPoster(p)" alt="" />
                    <div v-else class="composer-attachment-ph">
                      <SakuraIcon name="list" :size="18" />
                    </div>
                    <div class="composer-attachment-body">
                      <span class="composer-attachment-title">{{ p.title }}</span>
                      <span class="composer-attachment-sub">
                        {{ p.anime_count || p.items_count || 0 }} аниме
                      </span>
                    </div>
                    <button class="composer-attachment-remove" @click="removeComposerPlaylist(idx)" aria-label="Удалить"><SakuraIcon name="x" :size="16" /></button>
                  </div>
                  <div
                    v-for="(m, idx) in composerMedia"
                    :key="'media-' + idx"
                    class="composer-attachment"
                  >
                    <img v-if="m.type === 'image'" :src="m.url" alt="" />
                    <video v-else :src="m.url" muted></video>
                    <button class="composer-attachment-remove" @click="removeComposerMedia(idx)" aria-label="Удалить"><SakuraIcon name="x" :size="16" /></button>
                  </div>
                </div>

                <div class="composer-footer">
                  <div v-if="composerError" class="composer-error">
                    <SakuraIcon name="x-circle" :size="14" />
                    {{ composerError }}
                  </div>

                </div>
                <div v-for="row in composerExcerpts" :key="row.id"><ExcerptCard :excerpt="row" owner preview /><button @click="composerExcerpts = composerExcerpts.filter(item => item.id !== row.id)">Убрать отрывок</button></div>
                                <AttachModal
                  v-if="attachModalVisible"
                  v-model="editingAttachTab"
                  :selected-excerpts="selectedExcerpts"
                  @update:selectedExcerpts="selectedExcerpts = $event"
                  :selected-animes="selectedAnimes"
                  :selected-playlists="selectedPlaylists"
                  :selected-media-files="selectedMediaFiles"
                  @update:selectedAnimes="selectedAnimes = $event"
                  @update:selectedPlaylists="selectedPlaylists = $event"
                  @update:selectedMediaFiles="selectedMediaFiles = $event"
                  @close="attachModalVisible = false"
                  @confirm="onAttachConfirm"
                />
              </div>
            </div>
              <div class="posts-list" ref="postsContainer">
              <div v-if="loading && posts.length === 0" class="loading-state">
                <div class="skeleton-post" v-for="i in 3" :key="i">
                  <div class="skeleton-header">
                    <div class="skeleton-avatar"></div>
                    <div class="skeleton-info">
                      <div class="skeleton-line short"></div>
                      <div class="skeleton-line"></div>
                    </div>
                  </div>
                  <div class="skeleton-content">
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line medium"></div>
                  </div>
                </div>
              </div>

              <div v-else-if="!loading && visiblePosts.length === 0" class="empty-state">
                <div class="empty-icon"> <SakuraIcon name="file-text" :size="56" /> </div>
                <h3>Пока нет постов</h3>
                <p>Подпишитесь на интересных авторов или создайте свой первый пост!</p>
                <button @click="openCreatePostModal()" class="btn-primary">Создать пост</button>
              </div>

              <div v-else>
                <div v-if="newPostsCount > 0" class="new-posts-bar" @click="loadNewPosts">
                  <span>Показать {{ newPostsCount }} новых постов</span>
                </div>

                <VirtualFeed :items="visiblePosts" v-slot="{ item: post }">
                <PostCard
                  :post="post"
                  :data-post-id="post.id"
                  :like-loading="postStore.reactions.has(String(post.id))"
                  :dislike-loading="postStore.reactions.has(String(post.id))"
                  @like="handleLike"
                  @dislike="handleDislike"
                  @bookmark="toggleBookmark"
                  @comment="openComments"
                  @menu="openPostMenu"
                />
                </VirtualFeed>

                <div v-if="hasMore" class="load-more">
                  <button @click="loadMorePosts(true)" :disabled="loadingMore" class="btn-load-more">
                    {{ loadingMore ? 'Загрузка...' : posts.length >= 200 ? 'Следующие публикации' : 'Показать ещё' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
        <aside class="feed-right-sidebar">
          <div class="sidebar-card profile-summary">
            <div class="profile-summary-top">
              <img :src="currentUser?.avatar || defaultAvatar" class="profile-summary-avatar" alt="">
              <div class="profile-summary-info">
                <h4>{{ currentUser?.display_name || currentUser?.username }}</h4>
                <!-- <span class="profile-summary-username">@{{ currentUser?.username }}</span> -->
              </div>
            </div>
            <div class="profile-summary-stats">
              <div class="stat-item">
                <span class="stat-value">{{ currentUser?.followers_count ?? 0 }}</span>
                <span class="stat-label">Подписчики</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ currentUser?.following_count ?? 0 }}</span>
                <span class="stat-label">Подписки</span>
              </div>
            </div>
          </div>

        <!-- <div class="sidebar-card trending">
          <div class="trending-header">
            <h3 class="sidebar-title"><SakuraIcon name="fire" :size="16" /> Популярное</h3>
          </div>

          <div v-if="loadingMatchingChannels" class="trending-loading">
            <div class="trending-skeleton" v-for="i in 5" :key="i">
              <div class="skeleton-avatar"></div>
              <div class="skeleton-content">
                <div class="skeleton-line"></div>
                <div class="skeleton-line short"></div>
              </div>
            </div>
          </div>

          <div v-else-if="matchingChannels.length === 0" class="trending-empty">
            <SakuraIcon name="fire" :size="32" />
            <p>Пока нет подходящих каналов</p>
          </div>

          <div v-else class="matching-channels-list">
            <div
              v-for="(channel, idx) in matchingChannels"
              :key="channel.user_id"
              class="matching-channel-item"
              @click="openChannel(channel)"
            >
              <span class="matching-channel-rank">{{ idx + 1 }}</span>
              <img
                :src="channel.avatar || defaultAvatar"
                :alt="channel.display_name"
                class="matching-channel-avatar"
              />
              <div class="matching-channel-info">
                <span class="matching-channel-name">{{ channel.display_name }}</span>
                <span class="matching-channel-username">@{{ channel.username }}</span>
                <div v-if="channel.match_reasons.length" class="matching-channel-reasons">
                  <span
                    v-for="reason in channel.match_reasons"
                    :key="reason"
                    class="matching-reason-tag"
                  >
                    {{ reason }}
                  </span>
                </div>
              </div>
              <div class="matching-channel-stats">
                <span class="matching-posts-count">{{ formatCount(channel.posts_count) }} постов</span>
                <button
                  v-if="!channel.is_following"
                  class="matching-follow-btn"
                  @click.stop="followChannel(channel)"
                >
                  Подписаться
                </button>
                <button
                  v-else
                  class="matching-follow-btn following"
                  @click.stop="unfollowChannel(channel)"
                >
                  Отписаться
                </button>
              </div>
            </div>
          </div>
        </div> -->
        </aside>
      </div>
    </div>

    <!-- Modals -->
    <!-- <CreatePostModal
      v-if="showCreatePost"
      :initial-type="createPostType"
      @close="showCreatePost = false"
      @created="onPostCreated"
    /> -->
    <EditPostModal ref="editModal" v-if="showEditPost && selectedPost" :post="selectedPost as any" @open-attach="openEditAttach" @close="showEditPost = false" @updated="onPostEdited" />
    <CommentsModal v-if="showComments" :post="selectedPost as any" @close="showComments = false" />
    <PostMenu v-if="showMenu && selectedPost" :post="selectedPost as any" @close="showMenu = false" @edit="editPost as any" @delete="deletePost as any" @hide="hidePost as any" @hide-author="hidePostByAuthor as any" @followed="fetchCurrentUser as any" />
    <ReportModal v-if="showReport" content-type="post" :content-id="selectedPost?.id" @close="showReport = false" />
    <PostDetailModal v-if="showPostDetail" :post="selectedPost as any" @close="showPostDetail = false" />

    <!-- Report Detail Modal -->
    <div v-if="showReportDetail" class="modal-overlay" @click="showReportDetail = false">
      <div class="report-detail-modal" @click.stop>
        <div class="modal-header">
          <h3>Рассмотрение жалобы #{{ selectedReport?.id }}</h3>
          <button class="close-btn" @click="showReportDetail = false" aria-label="Закрыть">
            <SakuraIcon name="x" :size="18" />
          </button>
        </div>
        <div class="modal-body">
          <div class="report-full-info">
            <p><strong>Тип контента:</strong> {{ getContentTypeLabel(selectedReport?.content_type) }}</p>
            <p><strong>Причина:</strong> {{ getReasonLabel(selectedReport?.reason) }}</p>
            <p v-if="selectedReport?.comment"><strong>Комментарий жалобы:</strong> {{ selectedReport.comment }}</p>
            <p>
              <strong>Жалобщик:</strong>
              <a
                v-if="selectedReport?.reporter?.url"
                :href="selectedReport.reporter.url"
                class="report-link"
                @click.prevent="router.push(selectedReport.reporter.url)"
              >@{{ selectedReport.reporter.username }}</a>
              <span v-else>@{{ selectedReport?.reporter?.username || selectedReport?.reporter_username || 'неизвестен' }}</span>
            </p>
            <p><strong>Дата:</strong> {{ formatDate(selectedReport?.created_at) }}</p>
          </div>
          <section v-if="selectedReport?.content_preview" class="reported-content">
            <div class="reported-content-header">
              <strong>Содержимое жалобы</strong>
              <a
                v-if="selectedReport.content_preview.url"
                :href="selectedReport.content_preview.url"
                class="report-open-link"
                @click.prevent="router.push(selectedReport.content_preview.url)"
              >Открыть оригинал</a>
              <span v-else-if="selectedReport.content_preview.available === false" class="report-unavailable">Оригинал недоступен</span>
            </div>
            <p v-if="selectedReport.content_preview.author?.username" class="reported-author">
              Автор: @{{ selectedReport.content_preview.author.nickname || selectedReport.content_preview.author.username }}
            </p>
            <h4 v-if="selectedReport.content_preview.title">{{ selectedReport.content_preview.title }}</h4>
            <div v-if="selectedReport.content_preview.text" class="reported-text">{{ selectedReport.content_preview.text }}</div>
            <div v-if="selectedReport.content_preview.media?.length" class="reported-media">
              <a
                v-for="(media, mediaIndex) in selectedReport.content_preview.media"
                :key="media.id ?? media.url ?? mediaIndex"
                :href="media.url || undefined"
                target="_blank"
                rel="noopener"
                class="reported-media-item"
              >
                <img v-if="media.type === 'image' && media.url" :src="media.url" :alt="media.caption || 'Вложение поста'" />
                <video v-else-if="media.url" :src="media.url" controls preload="metadata"></video>
                <span>{{ media.caption || (media.type === 'video' ? 'Открыть видео' : 'Открыть изображение') }}</span>
              </a>
            </div>
          </section>
          <div v-else class="reported-content report-unavailable">Содержимое не найдено и снимок жалобы отсутствует.</div>
          <div class="report-actions-full">
            <label>Действие:</label>
            <select v-model="reportAction" class="action-select">
              <option value="none">Только зафиксировать решение</option>
              <option value="warn_user">Вынести предупреждение</option>
              <option v-if="selectedReport?.content_type !== 'user'" value="delete_content">Удалить контент</option>
              <option value="delete_user">Деактивировать аккаунт автора</option>
            </select>
            <textarea v-model="moderationComment" maxlength="1000" placeholder="Итог рассмотрения — его увидит пользователь" class="comment-textarea"></textarea>
            <p v-if="reportDecisionError" class="report-decision-error" role="alert">{{ reportDecisionError }}</p>
            <button class="btn-submit" :disabled="reportDecisionSaving" @click="submitReportDecision">
              {{ reportDecisionSaving ? 'Применение...' : 'Принять решение' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import VirtualFeed from "@/components/common/VirtualFeed.vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { defineAsyncComponent, ref, computed, onMounted, onUnmounted, onActivated, onDeactivated, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiClient, { getMediaUrl, isRequestCancelled } from '@/api/client'
import animeApi from '@/api/anime'
import type { FeedPost, SubscriptionUser, NotInterestedUser, HiddenPost, ReportItem, AnimeCard, PlaylistCard, MatchingChannel, MatchingChannelsResponse } from '@/api/feed'
import PostCard from '@/components/feed/PostCard.vue'
const EditPostModal = defineAsyncComponent(() => import('@/components/feed/EditPostModal.vue'))
const CommentsModal = defineAsyncComponent(() => import('@/components/feed/CommentsModal.vue'))
const PostMenu = defineAsyncComponent(() => import('@/components/feed/PostMenu.vue'))
const ReportModal = defineAsyncComponent(() => import('@/components/feed/ReportModal.vue'))
const PostDetailModal = defineAsyncComponent(() => import('@/components/feed/PostDetailModal.vue'))
import ExcerptCard from '@/components/excerpts/ExcerptCard.vue'
import type { Excerpt } from '@/api/excerpts'
const AttachModal = defineAsyncComponent(() => import('@/components/feed/AttachModal.vue'))
import { postsApi, subscriptionsApi, bookmarksApi, feedApi, followsApi } from '@/api/feed'
import { normalizePost } from '@/utils/normalizers'
import { useAuthStore } from '@/stores/auth'
import { usePostStore } from '@/stores/posts'
import { publishPost } from '@/lib/postPublication'
import { postDraftGet, postDraftPut, type PostDraft } from '@/lib/postDrafts'
import { useCachedReads } from '@/composables/useCachedReads'
import { invalidateQueryGroups } from '@/lib/queryClient'
const auth = useAuthStore()
const postStore = usePostStore()
const editModal = ref<InstanceType<typeof EditPostModal> | null>(null)
const attachingToEdit = ref(false)
const feedActive = ref(true)
const read = useCachedReads(() => feedActive.value)
const composerClientId = ref<string>(crypto.randomUUID())
const composerProgress = ref(0)
const feedCursor = ref<string | null>(null)
let restoringComposer = true
let composerDraftTimer: ReturnType<typeof setTimeout> | undefined

import { TIMING } from '@/constants'

type Post = FeedPost & {
  image_file: string | null
  video_file: string | null
  is_following: boolean
}

interface User {
  id: number
  username: string
  display_name: string
  avatar: string
  followers_count?: number
  following_count?: number
  is_following: boolean
  hidden_at?: string
  reason?: string
  is_moderator?: boolean
  is_staff?: boolean
}


interface FilterState {
  myPosts: boolean
  subscriptions: boolean
  groups: boolean
  withAnime: boolean
  period: string
  sort: string
  tags: string[]
}

const router = useRouter()
const route = useRoute()

const posts = ref<Post[]>([])
const loading = ref(true)
const loadingMore = ref(false)
const hasMore = ref(true)
const page = ref(1)
const activeTab = ref('feed')
const newPostsCount = ref(0)
const newPostIds = new Set<string>()
const handleNewPost = (event: Event) => {
  if (!feedActive.value || route.name === 'post-detail') return
  const id = String((event as CustomEvent<{ post_id?: string }>).detail?.post_id || '')
  if (!id || newPostIds.has(id) || posts.value.some(post => String(post.id) === id)) return
  newPostIds.add(id)
  if (newPostIds.size > 1000) newPostIds.delete(newPostIds.values().next().value!)
  newPostsCount.value = Math.min(1000, newPostsCount.value + 1)
}

const showFilters = ref(false)
const filters = ref<FilterState>({
  myPosts: false,
  subscriptions: false,
  groups: false,
  withAnime: false,
  period: 'all',
  sort: 'new',
  tags: []
})

const favoritePosts = ref<Post[]>([])
const subscriptionsSubTab = ref<'profiles' | 'favorites'>('profiles')
const subscriptionsSearch = ref('')
const subscriptionsSort = ref('date')
const subscriptions = ref<SubscriptionUser[]>([])
const subscriptionsPage = ref(1)
const hasMoreSubscriptions = ref(false)
const loadingSubscriptions = ref(false)
const loadingMoreSubscriptions = ref(false)
const loadingFavoritePosts = ref(false)

const bookmarkedPosts = ref<Post[]>([])
const loadingBookmarks = ref(false)
const bookmarkSearch = ref('')

const pinnedPosts = ref<Post[]>([])
const loadingPinned = ref(false)

const notInterestedUsers = ref<NotInterestedUser[]>([])
const loadingNotInterested = ref(false)
const notInterestedSearch = ref('')
const notInterestedSubTab = ref<'profiles' | 'posts'>('profiles')
const hiddenPosts = ref<HiddenPost[]>([])
const loadingHiddenPosts = ref(false)

const loadingPopular = ref(false)
const popularChannels = ref<MatchingChannel[]>([])

const matchingChannels = ref<MatchingChannel[]>([])
const loadingMatchingChannels = ref(false)

const loadMatchingChannels = async () => {
  loadingMatchingChannels.value = true
  try {
    const { data } = await feedApi.getMatchingChannels(5)
    matchingChannels.value = data.results || []
  } catch (error) {
    if (!isRequestCancelled(error)) console.error('Error loading matching channels:', error)
    matchingChannels.value = []
  } finally {
    loadingMatchingChannels.value = false
  }
}

const openChannel = (channel: MatchingChannel) => {
  router.push(`/profile/${channel.username}`)
}

const followChannel = async (channel: MatchingChannel) => {
  try {
    await followsApi.toggleFollow(channel.user_id)
    channel.is_following = true
  } catch (error) {
    console.error('Error following channel:', error)
  }
}

const unfollowChannel = async (channel: MatchingChannel) => {
  try {
    await followsApi.toggleFollow(channel.user_id)
    channel.is_following = false
  } catch (error) {
    console.error('Error unfollowing channel:', error)
  }
}

const formatCount = (count: number): string => {
  if (count >= 1000000) return (count / 1000000).toFixed(1) + 'M'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K'
  return String(count)
}

const reports = ref<ReportItem[]>([])
const loadingReports = ref(false)
const reportsFilter = ref({ status: '', reason: '' })
const showReportDetail = ref(false)
const selectedReport = ref<ReportItem | null>(null)
const reportAction = ref('delete_content')
const moderationComment = ref('')
const reportDecisionSaving = ref(false)
const reportDecisionError = ref('')

const showCreatePost = ref(false)
const showEditPost = ref(false)
const showComments = ref(false)
const showMenu = ref(false)
const showReport = ref(false)
const showPostDetail = ref(false)
const createPostType = ref<string | null>(null)

const composerText = ref('')
const composerSubmitting = ref(false)
const composerError = ref('')
const composerInput = ref<HTMLTextAreaElement | null>(null)
const composerExcerpts = ref<Excerpt[]>([])
const selectedExcerpts = ref<Excerpt[]>([])
const composerAnimes = ref<AnimeCard[]>([])
const composerAnimeRatings = ref<(number | null)[]>([])
const composerPlaylists = ref<PlaylistCard[]>([])
const composerMedia = ref<{ type: string; url: string; file: File }[]>([])
const composerIsSpoiler = ref(false)
const composerSpoilerFor = ref('')
const composerCanSubmit = computed(
  () =>
    (composerText.value.trim().length > 0 ||
      composerAnimes.value.length > 0 ||
      composerPlaylists.value.length > 0 ||
      composerMedia.value.length > 0 || composerExcerpts.value.length > 0) &&
    composerText.value.length <= 5000,
)

const attachModalVisible = ref(false)
const editingAttachTab = ref<'anime' | 'playlist' | 'media' | 'excerpt'>('media')
const selectedAnimes = ref<AnimeCard[]>([])
const selectedPlaylists = ref<PlaylistCard[]>([])
const selectedMediaFiles = ref<{ type: string; url: string; file: File }[]>([])

const animeSearch = ref('')
const animeResults = ref<AnimeCard[]>([])
const animeLoading = ref(false)
const animeLoadingMore = ref(false)
const animePage = ref(1)
const animeTotalPages = ref(1)
let animeSearchTimeout: ReturnType<typeof setTimeout> | null = null

const playlistSearch = ref('')
const playlists = ref<PlaylistCard[]>([])
const playlistsLoading = ref(false)
let playlistSearchTimeout: ReturnType<typeof setTimeout> | null = null

const getAnimePoster = (anime: AnimeCard): string => {
  if (!anime) return ''
  if (anime.poster) return getMediaUrl(anime.poster) || anime.poster_url || ''
  return anime.poster_url ? getMediaUrl(anime.poster_url) || anime.poster_url : ''
}

const getPlaylistPoster = (playlist: PlaylistCard): string => {
  if (!playlist) return ''
  if (playlist.cover_image) return getMediaUrl(playlist.cover_image) || ''
  return playlist.poster_url ? getMediaUrl(playlist.poster_url) || '' : ''
}

const searchAnime = () => {
  if (animeSearchTimeout) clearTimeout(animeSearchTimeout)
  animeSearchTimeout = setTimeout(async () => {
    const q = animeSearch.value.trim()
    if (!q) {
      animeResults.value = []
      animePage.value = 1
      animeTotalPages.value = 1
      return
    }
    animePage.value = 1
    animeLoading.value = true
    try {
      const response = await animeApi.list({
        search: q,
        page: 1,
        page_size: 20,
        ordering: '-score',
      })
      animeResults.value = response.results || []
      animeTotalPages.value = response.total_pages || 1
    } catch {
      animeResults.value = []
      animeTotalPages.value = 1
    } finally {
      animeLoading.value = false
    }
  }, 300)
}

const loadMoreAnime = async () => {
  if (animeLoadingMore.value || animePage.value >= animeTotalPages.value) return
  animeLoadingMore.value = true
  animePage.value++
  try {
    const q = animeSearch.value.trim()
    const response = await animeApi.list({
      search: q,
      page: animePage.value,
      page_size: 20,
      ordering: '-score',
    })
    animeResults.value.push(...(response.results || []))
    animeTotalPages.value = response.total_pages || 1
  } catch {
    animePage.value--
  } finally {
    animeLoadingMore.value = false
  }
}

const selectAnime = (a: AnimeCard) => {
  const idx = selectedAnimes.value.findIndex((x) => x.id === a.id)
  if (idx >= 0) selectedAnimes.value.splice(idx, 1)
  else selectedAnimes.value.push(a)
}

const searchPlaylists = async () => {
  if (playlistSearchTimeout) clearTimeout(playlistSearchTimeout)
  playlistSearchTimeout = setTimeout(async () => {
    playlistsLoading.value = true
    try {
      const { data } = await apiClient.get('/playlists/playlists/my/')
      const list: PlaylistCard[] = Array.isArray(data)
        ? data
        : (data && (data as { results?: PlaylistCard[] }).results) || []
      const q = playlistSearch.value.trim().toLowerCase()
      playlists.value = q
        ? list.filter(
            (p) =>
              (p.title || '').toLowerCase().includes(q) ||
              (p.description || '').toLowerCase().includes(q),
          )
        : list
    } catch {
      playlists.value = []
    } finally {
      playlistsLoading.value = false
    }
  }, 200)
}

const selectPlaylist = (p: PlaylistCard) => {
  const idx = selectedPlaylists.value.findIndex((x) => x.id === p.id)
  if (idx >= 0) selectedPlaylists.value.splice(idx, 1)
  else selectedPlaylists.value.push(p)
}

const onMediaSelected = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  const originals = Array.from(input.files)
  input.value = ''
  const { prepareMediaFiles } = await import('@/lib/clientMediaConversion')
  for (const { file, kind } of await prepareMediaFiles(originals)) {
    if (kind === 'file') continue
    const type = kind
    selectedMediaFiles.value.push({ type, url: URL.createObjectURL(file), file })
  }
}

const removeMediaFile = (idx: number) => {
  const m = selectedMediaFiles.value[idx]
  if (!m) return
  const isFromComposer = composerMedia.value.some((c) => c.url === m.url)
  if (!isFromComposer) URL.revokeObjectURL(m.url)
  selectedMediaFiles.value.splice(idx, 1)
}

const openAttachModal = (type: 'anime' | 'playlist' | 'media' | 'excerpt') => {
  attachingToEdit.value = false;
  editingAttachTab.value = type;
  selectedExcerpts.value = [...composerExcerpts.value]
  selectedAnimes.value = [...composerAnimes.value]
  selectedPlaylists.value = [...composerPlaylists.value]
  selectedMediaFiles.value = composerMedia.value.map((m) => ({ ...m }))
  attachModalVisible.value = true
  if (type === 'playlist') searchPlaylists()
}

const switchAttachTab = (type: 'anime' | 'playlist' | 'media' | 'excerpt') => {
  if (type === 'playlist') searchPlaylists()
}

const closeAttachModal = () => {
  const composerUrls = new Set(composerMedia.value.map((m) => m.url))
  selectedMediaFiles.value.forEach((m) => {
    if (!composerUrls.has(m.url)) URL.revokeObjectURL(m.url)
  })
  attachModalVisible.value = false
}

const openEditAttach = (tab: 'anime' | 'playlist' | 'media' | 'excerpt') => {
  const editor = editModal.value;
  if (!editor) return;
  attachingToEdit.value = true;
  selectedExcerpts.value = [...editor.editAttachPreviewExcerpts];
  selectedAnimes.value = [...editor.editAttachPreviewAnime];
  selectedPlaylists.value = [...editor.editAttachPreviewPlaylist];
  selectedMediaFiles.value = [...editor.editAttachPreviewMedia] as typeof selectedMediaFiles.value;
  editingAttachTab.value = tab;
  attachModalVisible.value = true;
};
const onAttachConfirm = () => {
  if (attachingToEdit.value && editModal.value) {
    editModal.value.onAttachConfirmFromEdit(selectedAnimes.value, selectedPlaylists.value, selectedMediaFiles.value, selectedExcerpts.value);
    attachModalVisible.value = false;
    attachingToEdit.value = false;
    return;
  }
  confirmAttach();
};

const confirmAttach = () => {
  composerMedia.value.forEach((m) => {
    if (!selectedMediaFiles.value.some((s) => s.url === m.url))
      URL.revokeObjectURL(m.url)
  })
  composerExcerpts.value = [...selectedExcerpts.value]
  composerAnimes.value = [...selectedAnimes.value]
  composerPlaylists.value = [...selectedPlaylists.value]
  composerMedia.value = [...selectedMediaFiles.value]
  attachModalVisible.value = false
}

const clampRating = (idx: number) => {
  const v = composerAnimeRatings.value[idx]
  if (v == null || isNaN(v)) return
  const clamped = Math.max(0, Math.min(10, Math.round(v)))
  composerAnimeRatings.value[idx] = clamped
}

const removeComposerAnime = (idx: number) => {
  composerAnimes.value.splice(idx, 1)
  composerAnimeRatings.value.splice(idx, 1)
}

const removeComposerPlaylist = (idx: number) => {
  composerPlaylists.value.splice(idx, 1)
}

const removeComposerMedia = (idx: number) => {
  const m = composerMedia.value[idx]
  if (m) URL.revokeObjectURL(m.url)
  composerMedia.value.splice(idx, 1)
}

const autoResizeComposer = () => {
  const el = composerInput.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

const composerOwnerId = auth.user?.id
async function saveComposerDraft() {
  if (!composerOwnerId || restoringComposer) return
  await postDraftPut('drafts', `${composerOwnerId}:create`, {
    key: `${composerOwnerId}:create`, clientId: composerClientId.value, text: composerText.value,
    visibility: 'public', allowComments: true, isSpoiler: composerIsSpoiler.value, spoilerFor: composerSpoilerFor.value,
    files: composerMedia.value.map(item => item.file), anime: JSON.parse(JSON.stringify(composerAnimes.value)),
    excerpts: JSON.parse(JSON.stringify(composerExcerpts.value)),
    playlists: JSON.parse(JSON.stringify(composerPlaylists.value)), shorts: [], ratings: [...composerAnimeRatings.value],
  } satisfies PostDraft).catch(() => { composerError.value = 'Не удалось сохранить черновик на устройстве' })
}
watch([composerExcerpts, composerText, composerMedia, composerAnimes, composerAnimeRatings, composerPlaylists, composerIsSpoiler,
  composerSpoilerFor], () => {
  if (restoringComposer) return
  if (composerDraftTimer) clearTimeout(composerDraftTimer)
  composerDraftTimer = setTimeout(() => void saveComposerDraft(), 250)
}, { deep: true })
onMounted(async () => {
  const saved = auth.user?.id ? await postDraftGet<PostDraft>('drafts', `${auth.user.id}:create`).catch(() => undefined) : undefined
  if (saved) {
    composerClientId.value = saved.clientId; composerText.value = saved.text
    composerIsSpoiler.value = saved.isSpoiler; composerSpoilerFor.value = saved.spoilerFor
    composerExcerpts.value = (saved.excerpts || []) as Excerpt[]
  composerAnimes.value = saved.anime as AnimeCard[]; composerAnimeRatings.value = saved.ratings
    composerPlaylists.value = saved.playlists as PlaylistCard[]
    composerMedia.value = saved.files.map(file => ({ file, url: URL.createObjectURL(file), type: file.type.startsWith('image') ? 'image' : 'video' }))
  }
  restoringComposer = false
})
onUnmounted(() => {
  if (composerDraftTimer) clearTimeout(composerDraftTimer)
  void saveComposerDraft()
})

const submitComposerPost = async () => {
  if (!composerCanSubmit.value || composerSubmitting.value) return
  composerSubmitting.value = true
  composerError.value = ''
  try {
    const fd = new FormData()
    fd.append('text', composerText.value.trim())
    fd.append('is_spoiler', String(composerIsSpoiler.value))
    if (composerIsSpoiler.value && composerSpoilerFor.value.trim()) {
      fd.append('spoiler_description', composerSpoilerFor.value.trim())
    }
    fd.append('excerpt_ids', JSON.stringify(composerExcerpts.value.map(item => item.id)))
    fd.append('anime_ids', JSON.stringify(composerAnimes.value.map(item => item.id)))
    fd.append('anime_ratings', JSON.stringify(composerAnimeRatings.value))
    fd.append('playlist_ids', JSON.stringify(composerPlaylists.value.map(item => item.id)))
    const owner = auth.user?.id
    if (!owner) throw new Error('Войдите в аккаунт')
    await saveComposerDraft()
    const post = await publishPost(owner, composerClientId.value, fd,
      composerMedia.value.map(item => item.file), value => { composerProgress.value = value })
    posts.value.unshift(post as Post)
    composerClientId.value = crypto.randomUUID()
    composerText.value = ''
    composerMedia.value = []
    composerExcerpts.value = []
    composerAnimes.value = []
    composerAnimeRatings.value = []
    composerPlaylists.value = []
    composerIsSpoiler.value = false
    composerSpoilerFor.value = ''
    if (composerInput.value) composerInput.value.style.height = 'auto'
  } catch (e: unknown) {
    console.error('Error creating post:', e)
    composerError.value =
      (e as { response?: { data?: { detail?: string; error?: string } } })
        .response?.data?.detail ||
      (e as { response?: { data?: { detail?: string; error?: string } } })
        .response?.data?.error ||
      'Ошибка при публикации поста'
  } finally {
    composerSubmitting.value = false
  }
}

const selectedPost = ref<Post | null>(null)

const currentUser = ref<User | null>(auth.user as User | null)
watch(() => auth.user, user => { currentUser.value = user as User | null })
const defaultAvatar = '/img/default-avatar.svg'

const feedTabs = computed(() => {
  const tabs = [
    { id: 'feed',          label: 'Лента',        icon: 'home' },
    { id: 'subscriptions', label: 'Подписки',     icon: 'users' },
    { id: 'not_interested', label: 'Не интересно', icon: 'eye-off' }
  ]
  if (currentUser.value?.is_moderator || currentUser.value?.is_staff) {
    tabs.push({ id: 'reports', label: 'Жалобы', icon: 'shield' })
  }
  return tabs
})

const activeFilterTags = computed(() => {
  const tags: { key: string; label: string }[] = []
  filters.value.tags.forEach((tag, idx) => {
    tags.push({ key: `tag-${idx}`, label: '#' + tag })
  })
  if (filters.value.myPosts) tags.push({ key: 'myPosts', label: 'Мои посты' })
  if (filters.value.subscriptions) tags.push({ key: 'subscriptions', label: 'Подписки' })
  if (filters.value.groups) tags.push({ key: 'groups', label: 'Из групп' })
  if (filters.value.withAnime) tags.push({ key: 'withAnime', label: 'С аниме' })
  if (filters.value.period !== 'all') {
    const periodLabels: Record<string, string> = { month: 'Месяц', week: 'Неделя', day: 'День' }
    const label = periodLabels[filters.value.period]
    if (label) tags.push({ key: 'period', label })
  }
  if (filters.value.sort !== 'new') {
    const sortLabels: Record<string, string> = { old: 'Старые', best: 'Лучшие', discussed: 'Обсуждаемые' }
    const label = sortLabels[filters.value.sort]
    if (label) tags.push({ key: 'sort', label })
  }
  return tags
})

let currentFeedKey = ""
const loadPosts = async () => {
  loading.value = !posts.value.length
  try {
    const params: Record<string, string | number> = {
      page: 1,
      page_size: 20,
      include_count: 'false',
      sort: filters.value.sort,
      date_range: filters.value.period,
    }
    if (filters.value.myPosts) params.my_posts = 'true'
    if (filters.value.subscriptions) params.subscriptions = 'true'
    if (filters.value.groups) params.groups = 'true'
    if (filters.value.withAnime) params.with_anime = 'true'
    if (filters.value.tags.length) params.tags = filters.value.tags.join(',')
    const key = JSON.stringify(params)
    const sameFeed = currentFeedKey === key
    currentFeedKey = key
    if (!sameFeed) posts.value = []
    const saved = postStore.feeds.get(key)
    const restoring = saved && Date.now() - saved.savedAt < 15 * 60_000 && !posts.value.length
    if (restoring) {
      posts.value = saved.rows.map(normalizePost) as unknown as Post[]
      feedCursor.value = saved.cursor
      hasMore.value = !!saved.cursor
      loading.value = false
      await nextTick()
      requestAnimationFrame(() => window.scrollTo(0, saved.scroll))
    }
    await read(['feed', key], async signal => (await apiClient.get('/social/feed/extended/', { params, signal })).data, data => {
      if (currentFeedKey !== key) return
      const head = (data.results || []).map(normalizePost) as Post[]
      if (restoring || (sameFeed && posts.value.length > 20)) {
        const ids = new Set(head.map(row => String(row.id)))
        posts.value = [...head, ...posts.value.filter(row => !ids.has(String(row.id)))]
      } else {
        const headIds = new Set(head.map(row => String(row.id)))
        const preparing = posts.value.filter(row => !headIds.has(String(row.id)) &&
          (row.status === 'processing' || row.status === 'failed' || row.processing_media?.length))
        posts.value = [...preparing, ...head]
        hasMore.value = !!data.next_cursor
        feedCursor.value = data.next_cursor
      }
      newPostsCount.value = 0
      newPostIds.clear()
    })
  } catch (error) {
    if (isRequestCancelled(error)) return
    console.error('Error loading posts:', error)
    try {
      const response = await apiClient.get('/social/feed/weighted/')
      posts.value = (response.data.posts || response.data.results || []).map(normalizePost) as Post[]
    } catch (fallbackError) {
      if (!isRequestCancelled(fallbackError)) console.error('Fallback feed also failed:', fallbackError)
    }
  } finally {
    loading.value = false
  }
}

const loadMorePosts = async (nextSection = false) => {
  if (loadingMore.value || !hasMore.value) return
  if (posts.value.length >= 200) {
    if (!nextSection) return
    posts.value = []
    await nextTick()
    window.scrollTo(0, 0)
  }
  loadingMore.value = true
  try {
    const params: Record<string, string | number> = {
      cursor: feedCursor.value || '',
      page_size: 20,
      include_count: 'false',
      sort: filters.value.sort,
      date_range: filters.value.period,
    }
    if (filters.value.myPosts) params.my_posts = 'true'
    if (filters.value.subscriptions) params.subscriptions = 'true'
    if (filters.value.groups) params.groups = 'true'
    if (filters.value.withAnime) params.with_anime = 'true'
    if (filters.value.tags.length) params.tags = filters.value.tags.join(',')
    const response = await apiClient.get('/social/feed/extended/', {
      params
    })
    const newPosts = (response.data.results || []).map(normalizePost) as Post[]
    const seen = new Set(posts.value.map(row => String(row.id)))
    posts.value.push(...newPosts.filter(row => !seen.has(String(row.id))))
    feedCursor.value = response.data.next_cursor
    hasMore.value = !!feedCursor.value
    page.value++
  } catch (error) {
    if (!isRequestCancelled(error)) console.error('Error loading more posts:', error)
  } finally {
    loadingMore.value = false
  }
}

const loadNewPosts = async () => {
  page.value = 1
  await invalidateQueryGroups(['feed'])
  await loadPosts()
}

const switchTab = async (tabId: string) => {
  activeTab.value = tabId
  page.value = 1

  if (tabId === 'feed') {
    await loadPosts()
  } else if (tabId === 'popular') {
    await loadPopularChannels()
  } else if (tabId === 'subscriptions') {
    await loadSubscriptions()
  } else if (tabId === 'bookmarks') {
    await loadBookmarks()
  } else if (tabId === 'pinned') {
    await loadPinnedPosts()
  } else if (tabId === 'not_interested') {
    await loadNotInterested()
  } else if (tabId === 'reports') {
    await loadReports()
  }
}

const loadBookmarks = async () => {
  loadingBookmarks.value = true
  try {
    const { data } = await bookmarksApi.getPosts()
    bookmarkedPosts.value = (data.results || []).map(normalizePost) as unknown as Post[]
  } catch (e) {
    console.error('Error loading bookmarks:', e)
    bookmarkedPosts.value = []
  } finally {
    loadingBookmarks.value = false
  }
}

const filteredBookmarks = computed(() => {
  if (!bookmarkSearch.value.trim()) return bookmarkedPosts.value
  const q = bookmarkSearch.value.toLowerCase()
  return bookmarkedPosts.value.filter(p =>
    (p.text || '').toLowerCase().includes(q) ||
    (p.title || '').toLowerCase().includes(q)
  )
})

const loadPinnedPosts = async () => {
  loadingPinned.value = true
  try {
    const { data } = await apiClient.get('/social/posts/', { params: { pinned: true, my_pins: true } })
      pinnedPosts.value = (data.results || []).map(normalizePost) as Post[]
  } catch {
    try {
      const { data: me } = await apiClient.get('/users/me/')
      const { data: userPosts } = await apiClient.get('/social/posts/', { params: { author: me.id, is_pinned: true } })
      pinnedPosts.value = (userPosts.results || []).map(normalizePost) as Post[]
    } catch {
      pinnedPosts.value = []
    }
  } finally {
    loadingPinned.value = false
  }
}

const unpinPostFromTab = async (post: Post) => {
  try {
    await apiClient.post(`/social/posts/${post.id}/unpin/`)
    pinnedPosts.value = pinnedPosts.value.filter(p => p.id !== post.id)
  } catch (error) {
    console.error('Error unpinning:', error)
  }
}

const loadPopularChannels = async () => {
  loadingPopular.value = true
  try {
    const { data } = await feedApi.getMatchingChannels(5)
    popularChannels.value = data.results || []
  } catch (error) {
    console.error('Error loading popular channels:', error)
    popularChannels.value = []
  } finally {
    loadingPopular.value = false
  }
}

const loadFavoritePosts = async () => {
  loadingFavoritePosts.value = true
  try {
    const { data } = await bookmarksApi.getPosts()
    favoritePosts.value = (data.results || []).map(normalizePost) as unknown as Post[]
  } catch (error) {
    console.error('Error loading favorite posts:', error)
    favoritePosts.value = []
  } finally {
    loadingFavoritePosts.value = false
  }
}

const loadHiddenPosts = async () => {
  loadingHiddenPosts.value = true
  try {
    const { data } = await subscriptionsApi.getHiddenPosts()
    hiddenPosts.value = data.results || []
  } catch (error) {
    console.error('Error loading hidden posts:', error)
    hiddenPosts.value = []
  } finally {
    loadingHiddenPosts.value = false
  }
}

const restorePost = async (postId: string | number) => {
  try {
    await subscriptionsApi.restoreHiddenPost(postId)
    hiddenPosts.value = hiddenPosts.value.filter(p => p.post_id !== postId)
  } catch (error) {
    console.error('Error restoring post:', error)
  }
}

const openHiddenPost = (item: HiddenPost) => {
  if (item.post_id) {
    router.push(`/post/${item.post_id}`)
  }
}

const applyFilters = () => {
  page.value = 1
  loadPosts()
}

const tagInput = ref('')

const normalizeTag = (raw: string) => raw.trim().replace(/^#/, '').replace(/\s+/g, '-')

const addTag = () => {
  const raw = tagInput.value
  if (!raw.trim()) return
  const parts = raw.split(/[,\s]+/).filter(Boolean)
  let changed = false
  for (const part of parts) {
    const tag = normalizeTag(part)
    if (tag && !filters.value.tags.includes(tag)) {
      filters.value.tags.push(tag)
      changed = true
    }
  }
  if (changed) {
    applyFilters()
  }
  tagInput.value = ''
}

const clearAllTags = () => {
  filters.value.tags = []
  applyFilters()
}

const handleTagBackspace = (e: KeyboardEvent) => {
  if (!tagInput.value && filters.value.tags.length) {
    filters.value.tags.pop()
    applyFilters()
  }
}

const visiblePosts = computed(() => {
  const tags = filters.value.tags
  const visible = posts.value.filter(post => !post.is_deleted && post.status !== 'processing' && post.status !== 'failed')
  if (!tags.length) return visible
  return visible.filter((post) => {
    const postTags = (post.hashtags || []).map((t) => t.toLowerCase().replace(/^#/, '').trim())
    return tags.every((tag) => postTags.includes(tag.toLowerCase().trim()))
  })
})

const toggleFilter = (key: keyof FilterState) => {
  if (key === 'myPosts') filters.value.myPosts = !filters.value.myPosts
  else if (key === 'subscriptions') filters.value.subscriptions = !filters.value.subscriptions
  else if (key === 'groups') filters.value.groups = !filters.value.groups
  else if (key === 'withAnime') filters.value.withAnime = !filters.value.withAnime
  applyFilters()
}

const removeFilter = (key: string) => {
  if (key.startsWith('tag-')) {
    const idx = parseInt(key.replace('tag-', ''), 10)
    if (!isNaN(idx) && idx < filters.value.tags.length) {
      filters.value.tags.splice(idx, 1)
    }
    applyFilters()
    return
  }
  if (key === 'myPosts') filters.value.myPosts = false
  else if (key === 'subscriptions') filters.value.subscriptions = false
  else if (key === 'groups') filters.value.groups = false
  else if (key === 'withAnime') filters.value.withAnime = false
  else if (key === 'period') filters.value.period = 'all'
  else if (key === 'sort') filters.value.sort = 'new'
  applyFilters()
}

const clearAllFilters = () => {
  filters.value = { myPosts: false, subscriptions: false, groups: false, withAnime: false, period: 'all', sort: 'new', tags: [] }
  tagInput.value = ''
  if (route.query.tag) {
    router.replace({ path: route.path, query: { ...route.query, tag: undefined } })
  }
  applyFilters()
}

const loadSubscriptions = async () => {
  loadingSubscriptions.value = true
  try {
    const { data } = await subscriptionsApi.getSubscriptions(subscriptionsPage.value, subscriptionsSearch.value, subscriptionsSort.value)
    subscriptions.value = data.results || []
    hasMoreSubscriptions.value = !!data.next
  } catch (error) {
    console.error('Error loading subscriptions:', error)
  } finally {
    loadingSubscriptions.value = false
  }
}

const loadMoreSubscriptions = async () => {
  if (loadingMoreSubscriptions.value || !hasMoreSubscriptions.value) return
  loadingMoreSubscriptions.value = true
  try {
    subscriptionsPage.value++
    const { data } = await subscriptionsApi.getSubscriptions(subscriptionsPage.value, subscriptionsSearch.value, subscriptionsSort.value)
    subscriptions.value.push(...(data.results || []))
    hasMoreSubscriptions.value = !!data.next
  } catch (error) {
    console.error('Error loading more subscriptions:', error)
  } finally {
    loadingMoreSubscriptions.value = false
  }
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null
const debouncedSearchSubscriptions = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    subscriptionsPage.value = 1
    loadSubscriptions()
  }, TIMING.DEBOUNCE_SHORT)
}

const unfollowUser = async (userId: number) => {
  try {
    await subscriptionsApi.unfollow(userId)
    subscriptions.value = subscriptions.value.filter(u => u.id !== userId)
  } catch (error) {
    console.error('Error unfollowing:', error)
  }
}

const openChat = async (userId: number) => {
  try {
    const response = await apiClient.post('/social/private-chats/', { user2: userId })
    router.push(`/chats/${response.data.id}`)
  } catch (error) {
    console.error('Error creating chat:', error)
    alert('Не удалось создать чат')
  }
}

const loadNotInterested = async () => {
  loadingNotInterested.value = true
  try {
    const { data } = await subscriptionsApi.getNotInterested(1, notInterestedSearch.value)
    notInterestedUsers.value = data.results || []
  } catch (error) {
    console.error('Error loading not interested:', error)
  } finally {
    loadingNotInterested.value = false
  }
}

const debouncedSearchNotInterested = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadNotInterested()
  }, TIMING.DEBOUNCE_SHORT)
}

const unhideUser = async (userId: number) => {
  try {
    await subscriptionsApi.removeNotInterested(userId)
    notInterestedUsers.value = notInterestedUsers.value.filter(u => u.id !== userId)
  } catch (error) {
    console.error('Error unhiding user:', error)
  }
}

const goToProfile = (userId: number) => {
  router.push(`/profile/${userId}`)
}

const loadReports = async () => {
  loadingReports.value = true
  try {
    const { data } = await subscriptionsApi.getReports({
      status: reportsFilter.value.status || undefined,
      reason: reportsFilter.value.reason || undefined
    })
    reports.value = data.results || []
  } catch (error) {
    console.error('Error loading reports:', error)
  } finally {
    loadingReports.value = false
  }
}

const openReportDetail = (report: ReportItem) => {
  selectedReport.value = report
  reportAction.value = report.content_type === 'user' ? 'warn_user' : 'delete_content'
  moderationComment.value = ''
  reportDecisionError.value = ''
  showReportDetail.value = true
}

const rejectReport = async (reportId: number) => {
  try {
    await subscriptionsApi.rejectReport(reportId)
    reports.value = reports.value.filter(r => r.id !== reportId)
  } catch (error) {
    console.error('Error rejecting report:', error)
  }
}

const submitReportDecision = async () => {
  if (!selectedReport.value) return
  if (!moderationComment.value.trim()) {
    reportDecisionError.value = 'Укажите итог рассмотрения — он будет отправлен пользователю.'
    return
  }
  reportDecisionSaving.value = true
  reportDecisionError.value = ''
  try {
    await subscriptionsApi.resolveReport(selectedReport.value.id, reportAction.value, moderationComment.value.trim())
    showReportDetail.value = false
    await loadReports()
  } catch (error) {
    console.error('Error resolving report:', error)
    const response = (error as { response?: { data?: { error?: string; detail?: string } } }).response
    reportDecisionError.value = response?.data?.error || response?.data?.detail || 'Не удалось применить решение.'
  } finally {
    reportDecisionSaving.value = false
  }
}

const getContentTypeLabel = (type?: string) => {
  const labels: Record<string, string> = { post: 'Пост', comment: 'Комментарий', user: 'Пользователь' }
  return labels[type || ''] || type
}

const getStatusLabel = (status?: string) => {
  const labels: Record<string, string> = { pending: 'Новая', in_progress: 'В процессе', resolved: 'Рассмотрена', rejected: 'Отклонена' }
  return labels[status || ''] || status
}

const getReasonLabel = (reason?: string) => {
  const labels: Record<string, string> = { copyright: 'Авторские права', inappropriate: 'Неприемлемый контент', spam: 'Спам', harassment: 'Оскорбления', spoiler: 'Спойлер', other: 'Другое' }
  return labels[reason || ''] || reason
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('ru-RU')
}

const openCreatePostModal = () => {
}

const openComments = (post: Post) => { selectedPost.value = post; showComments.value = true }
const openPostMenu = (post: Post) => { selectedPost.value = post; showMenu.value = true }

const loadPostFromRoute = async () => {
  const postId = route.params.id || route.name === 'post-detail' ? route.params.id : null
  if (!postId) return

  try {
    const { data } = await apiClient.get(`/social/posts/${postId}/`)
    const post = normalizePost(data) as unknown as Post

    if (posts.value.length === 0) {
      await loadPosts()
    }

    const existingIndex = posts.value.findIndex(p => String(p.id) === String(postId))
    if (existingIndex === -1) {
      posts.value.unshift(post)
    }

    await nextTick()

    setTimeout(() => {
      const postElement = document.querySelector(`[data-post-id="${postId}"]`)
      if (postElement) {
        postElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
        postElement.classList.add('highlight-post')
        setTimeout(() => postElement.classList.remove('highlight-post'), 3000)
      }
    }, 100)
  } catch (error) {
    console.error('Error loading post from route:', error)
    await loadPosts()
  }
}


const handleLike = async (post: Post) => {
  try { await postStore.react(post, 'like') } catch (error) { console.error('Ошибка реакции', error) }
}
const handleDislike = async (post: Post) => {
  try { await postStore.react(post, 'dislike') } catch (error) { console.error('Ошибка реакции', error) }
}

const toggleBookmark = async (post: Post) => {
  try {
    const response = await apiClient.post('/social/bookmarks/toggle/', { post_id: post.id, active: !post.is_bookmarked, client_action_id: crypto.randomUUID() })
    post.is_bookmarked = response.data.bookmarked
  } catch (error) {
    console.error('Error toggling bookmark:', error)
  }
}



const editPost = (post: Post) => {
  selectedPost.value = post
  showMenu.value = false
  showEditPost.value = true
}

const onPostEdited = (updatedPost: FeedPost | null | undefined) => {
  if (!updatedPost || !updatedPost.id) return
  const postId: string | number = updatedPost.id
  const idx = posts.value.findIndex(p => p.id === postId)
  if (idx !== -1) {
    const updated = { ...posts.value[idx], ...updatedPost }
    posts.value[idx] = updated as typeof posts.value[number]
  }
  bookmarkedPosts.value = bookmarkedPosts.value.map(p =>
    p.id === updatedPost.id ? { ...p, ...updatedPost } : p
  )
  pinnedPosts.value = pinnedPosts.value.map(p =>
    p.id === updatedPost.id ? { ...p, ...updatedPost } : p
  )
  favoritePosts.value = favoritePosts.value.map(p =>
    p.id === updatedPost.id ? { ...p, ...updatedPost } : p
  )
  showEditPost.value = false
}
const deletePost = async (post: Post) => {
  const originalPosts = [...posts.value]

  try {
    posts.value = posts.value.filter(p => p.id !== post.id)
    showMenu.value = false

    await apiClient.delete(`/social/posts/${post.id}/`)

  } catch (e: unknown) {
    console.error('Error deleting post:', e)
    posts.value = originalPosts
    alert('Произошла ошибка при удалении поста. Пожалуйста, попробуйте позже.')
  }
}
const hidePost = async (post: Post) => {
  try {
    await postsApi.notInterestedPost(post.id)
    posts.value = posts.value.filter(p => p.id !== post.id)
    hiddenPosts.value.unshift({
      id: `hidden:${post.id}`,
      post_id: post.id,
      post_preview: post.text.slice(0, 200) || '',
      hidden_at: new Date().toISOString(),
    })
  } catch (error) {
    console.error('Error hiding post:', error)
    alert('Не удалось скрыть пост. Попробуйте ещё раз.')
  } finally {
    showMenu.value = false
  }
}

const hidePostByAuthor = async (post: Post) => {
  try {
    await apiClient.post(`/social/users/${post.author}/hide/`)
    posts.value = posts.value.filter(p => p.author !== post.author)
  } catch (error) {
    console.error('Error hiding author:', error)
    alert('Не удалось скрыть автора. Попробуйте ещё раз.')
  } finally {
    showMenu.value = false
  }
}

const onPostCreated = (post: Post) => { posts.value.unshift(post); showCreatePost.value = false }

const fetchCurrentUser = async () => {
  await auth.checkAuth()
  currentUser.value = auth.user as User | null
}

const handleScroll = () => {
  const scrollTop = window.scrollY
  const windowHeight = window.innerHeight ?? 0
  const documentHeight = document.documentElement.scrollHeight
  if (scrollTop + windowHeight >= documentHeight - 500) {
    if (activeTab.value === 'feed') loadMorePosts()
    else if (activeTab.value === 'subscriptions') loadMoreSubscriptions()
  }
}

onMounted(async () => {
  void fetchCurrentUser()

  const tag = route.query.tag
  if (typeof tag === 'string' && tag.trim()) {
    filters.value.tags = [tag.replace(/^#/, '').trim()]
  }

  const postId = route.params.id
  if (postId && route.name === 'post-detail') {
    await loadPostFromRoute()
  } else {
    await loadPosts()
  }

  if (!feedActive.value) return
  loadMatchingChannels()

  window.addEventListener('scroll', handleScroll)
  window.addEventListener('new_post', handleNewPost)
})

watch(
  () => route?.query?.tag,
  (tag) => {
    if (!feedActive.value) return
    const next = typeof tag === 'string' ? tag.replace(/^#/, '').trim() : ''
    if (next && !filters.value.tags.includes(next)) {
      filters.value.tags = [next]
      if (activeTab.value === 'feed') applyFilters()
    } else if (!next && filters.value.tags.length) {
      filters.value.tags = []
      if (activeTab.value === 'feed') applyFilters()
    }
  },
)

const feedSession = postStore.sessionGeneration
let feedScroll = 0
let activatedOnce = false
onActivated(() => {
  feedActive.value = true
  if (!activatedOnce) { activatedOnce = true; return }
  window.addEventListener('scroll', handleScroll)
  requestAnimationFrame(() => window.scrollTo(0, feedScroll))
  void switchTab(activeTab.value)
})
onDeactivated(() => {
  feedActive.value = false
  feedScroll = window.scrollY
  window.removeEventListener('scroll', handleScroll)
})
onUnmounted(() => {
  window.removeEventListener('new_post', handleNewPost)
  window.removeEventListener('scroll', handleScroll)
  if (feedSession !== postStore.sessionGeneration) return
  const params: Record<string, string | number> = { page: 1, page_size: 20, include_count: 'false', sort: filters.value.sort, date_range: filters.value.period }
  if (filters.value.myPosts) params.my_posts = 'true'
  if (filters.value.subscriptions) params.subscriptions = 'true'
  if (filters.value.groups) params.groups = 'true'
  if (filters.value.withAnime) params.with_anime = 'true'
  if (filters.value.tags.length) params.tags = filters.value.tags.join(',')
  postStore.feeds.set(JSON.stringify(params), { rows: posts.value.slice(-200), cursor: feedCursor.value, scroll: window.scrollY, savedAt: Date.now() })
  if (postStore.feeds.size > 3) postStore.feeds.delete(postStore.feeds.keys().next().value!)
})
</script>

<style scoped>
.dots {
  animation: pulse 1.4s infinite;
}
@keyframes pulse {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
}
.feed-page {
  min-height: 100vh;
  background: var(--surface-1);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1rem;
  padding: 1.75rem 0 1.25rem;
  flex-wrap: wrap;
}

.page-header-text {
  flex: 1;
  min-width: 200px;
}

.page-title {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  background: linear-gradient(135deg, var(--accent-bright) 0%, var(--accent) 50%, var(--accent-press) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.page-subtitle {
  margin: 0.35rem 0 0;
  font-size: 0.9rem;
  color: var(--text-tertiary);
}

.feed-tabs {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
  padding: 0.4rem;
  margin-bottom: 0.25rem;
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: transparent;
  border: none;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-lg);
  transition: all var(--duration-base) var(--ease-petal);
}

.tab-btn:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.tab-btn.active {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  box-shadow: var(--shadow-petal-sm);
}

.tab-btn :deep(.sakura-icon) {
  transition: color var(--duration-base) var(--ease-petal);
}

.tab-btn.active :deep(.sakura-icon) {
  color: var(--text-on-accent);
}

.new-posts-badge {
  background: linear-gradient(135deg, var(--danger) 0%, #ff6b6b 100%);
  color: white;
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border-radius: var(--radius-full);
  box-shadow: 0 2px 8px rgba(255,138,138,0.3);
}

.btn-create-post {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  border: none;
  padding: 0.75rem 1.25rem;
  border-radius: var(--radius-lg);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  box-shadow: var(--shadow-petal-sm);
}

.btn-create-post:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow-sm);
}

.btn-create-post :deep(.sakura-icon) {
  color: var(--text-on-accent);
}

.filters-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.3rem 0.55rem;
  margin-top: 0.75rem;
  gap: 0.5rem;
  flex-wrap: wrap;
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.filters-section {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-weight: 500;
  transition: all var(--duration-base) var(--ease-petal);
}

.filter-toggle:hover {
  background: var(--surface-5);
  border-color: var(--accent);
  color: var(--accent);
}

.filter-toggle :deep(.sakura-icon) {
  transition: color var(--duration-base) var(--ease-petal);
}

.filter-toggle:hover :deep(.sakura-icon) {
  color: var(--accent);
}

.filter-toggle .arrow {
  transition: transform var(--duration-base) var(--ease-petal);
}

.filter-toggle .arrow.open {
  transform: rotate(180deg);
}

.filters-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 0.5rem;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 1rem;
  z-index: 20;
  min-width: 200px;
  box-shadow: var(--shadow-lg);
}

.filter-group {
  margin-bottom: 1rem;
}

.filter-group:last-child {
  margin-bottom: 0;
}

.filter-label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-tertiary);
  font-size: 0.85rem;
}

.tag-filter-inline {
  display: flex;
  align-items: center;
}

.tag-filter-inline .tag-input-wrapper {
  display: flex;
  align-items: center;
  gap: 0.15rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 0.01rem 0.35rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.tag-filter-inline .tag-input-wrapper:focus-within {
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.tag-filter-inline .tag-icon {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.tag-filter-inline .tag-input {
  background: transparent;
  border: none;
  color: var(--text-primary);
  padding: 0;
  font-size: 0.85rem;
  outline: none;
  width: 120px;
}

.tag-filter-inline .tag-input::placeholder {
  color: var(--text-tertiary);
}

.tag-filter-inline .tag-clear-all {
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  border-radius: var(--radius-sm);
  transition: all var(--duration-base) var(--ease-petal);
}

.tag-filter-inline .tag-clear-all:hover {
  color: var(--danger);
  background: var(--danger-subtle);
}

.toggle-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  padding: 0.5rem 0.85rem;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 0.85rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.toggle-btn:hover {
  background: var(--surface-5);
  border-color: var(--accent);
}

.toggle-btn.active {
  background: var(--accent-subtle);
  color: var(--accent);
  border-color: var(--accent);
}

.toggle-btn :deep(.sakura-icon) {
  transition: color var(--duration-base) var(--ease-petal);
}

.toggle-btn.active :deep(.sakura-icon) {
  color: var(--accent);
}

.period-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.period-btn {
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 0.85rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.period-btn:hover {
  background: var(--surface-5);
  border-color: var(--accent);
}

.period-btn.active {
  background: var(--accent-subtle);
  color: var(--accent);
  border-color: var(--accent);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.3rem 0;
  color: var(--text-secondary) !important;
  transition: color var(--duration-base) var(--ease-petal);
}

.checkbox-label:hover {
  color: var(--accent) !important;
}

.checkbox-label input {
  accent-color: var(--accent);
}

.filter-select, .sort-select {
  background: var(--surface-4);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  padding: 0.5rem 0.85rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 0.85rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.filter-select:hover, .sort-select:hover {
  border-color: var(--accent);
}

.filter-select:focus, .sort-select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.sort-section {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.sort-section-label {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding-bottom: 1rem;
  align-items: center;
}

.filter-tag {
  background: var(--surface-4);
  color: var(--text-secondary);
  padding: 0.3rem 0.8rem;
  border-radius: var(--radius-full);
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.filter-tag:hover {
  background: var(--accent-subtle);
  color: var(--accent);
}

.clear-all {
  background: none;
  border: none;
  color: var(--accent);
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
}

.clear-all:hover {
  text-decoration: underline;
}

/* Sub-tabs */
.sub-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0.5rem;
}

.sub-tab-btn {
  background: none;
  border: none;
  color: var(--text-tertiary);
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all var(--duration-base) var(--ease-petal);
}

.sub-tab-btn:hover {
  background: var(--surface-4);
  color: var(--text-secondary);
}

.sub-tab-btn.active {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  box-shadow: var(--shadow-petal-sm);
}

.sub-tab-btn.active :deep(.sakura-icon) {
  color: var(--text-on-accent) !important;
}

/* Subscription cards */
.subscription-card.clickable {
  cursor: pointer;
}

.subscription-card.clickable:hover {
  background: var(--surface-4);
}

.subscription-card.blocked {
  border: 1px solid var(--danger-subtle);
  background: rgba(255,138,138,0.05);
}

.subscription-card.blocked .user-info h4 {
  color: var(--danger);
}

.btn-unblock {
  background: linear-gradient(135deg, var(--danger) 0%, #ff6b6b 100%);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all var(--duration-base) var(--ease-petal);
}

.btn-unblock:hover {
  box-shadow: 0 0 12px rgba(255,138,138,0.3);
}

/* Hidden post cards */
.hidden-post-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--surface-3);
  border-radius: var(--radius-lg);
  padding: 1rem;
  margin-bottom: 0.5rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.hidden-post-card:hover {
  background: var(--surface-4);
}

.hidden-post-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  cursor: pointer;
}

.hidden-post-info:hover .hidden-post-title {
  color: var(--accent);
}

.hidden-post-title {
  color: var(--text-primary);
  font-size: 0.9rem;
}

.hidden-date {
  color: var(--text-tertiary);
  font-size: 0.8rem;
}

.btn-restore {
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  padding: 0.4rem 0.8rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 0.8rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.btn-restore:hover {
  background: var(--accent-subtle);
  color: var(--accent);
  border-color: var(--accent);
}

.feed-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 1.5rem;
  padding: 1.25rem 0;
}

@media (min-width: 900px) {
  .feed-layout {
    grid-template-columns: minmax(0, 1fr) 280px;
  }
}

.feed-main {
  min-width: 0;
  min-height: 500px;
}

.composer-card {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 1rem;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: var(--shadow-sm-card);
  transition: all var(--duration-base) var(--ease-petal);
}

.composer-card:focus-within {
  border-color: var(--accent);
  box-shadow: var(--shadow-petal-sm);
}

.composer-card:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-petal-sm);
}

.composer-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--accent);
  flex-shrink: 0;
}

.composer-body {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex: 1;
  flex-wrap: wrap;
  min-width: 0;
}

.composer-field {
  min-width: 0;
  display: block;
  width: 100%;
  flex: 1;
  min-height: 40px;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 0.7rem 1rem;
  color: var(--text-primary);
  font-size: 0.95rem;
  font-family: inherit;
  line-height: 1.5;
  resize: none;
  overflow-y: hidden;
  cursor: text;
  transition: all var(--duration-base) var(--ease-petal);
}

.composer-field::placeholder {
  color: var(--text-tertiary);
}

.composer-field:hover {
  border-color: var(--accent);
  background: var(--surface-5);
}

.composer-field:focus {
  outline: none;
  border-color: var(--accent);
  background: var(--surface-5);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

.composer-actions {
  display: flex;
  flex-wrap: wrap;
  max-width: 100%;
  gap: 0.5rem;
  margin-top: 0.6rem;
}

.composer-hashtag-hint {
  flex-basis: 100%;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-tertiary, #888);
}

.composer-action {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: none;
  border: none;
  color: var(--text-tertiary);
  font-size: 0.8rem;
  padding: 0.35rem 0.6rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.composer-action:hover {
  background: var(--accent-subtle);
  color: var(--accent);
}

.composer-action :deep(.sakura-icon) {
  transition: color var(--duration-base) var(--ease-petal);
}

.composer-action:hover :deep(.sakura-icon) {
  color: var(--accent);
}

.composer-spoiler-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
  color: var(--text-tertiary);
  font-size: 0.8rem;
  cursor: pointer;
  user-select: none;
  padding: 0.35rem 0.6rem;
  border-radius: var(--radius-md);
  transition: color var(--duration-base) var(--ease-petal);
}

.composer-spoiler-toggle:hover {
  color: var(--text-secondary);
}

.toggle-input {
  display: none;
}

.toggle-switch {
  position: relative;
  width: 34px;
  height: 19px;
  background: var(--surface-5);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  transition: all var(--duration-base) var(--ease-petal);
  flex-shrink: 0;
}

.toggle-slider {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 13px;
  height: 13px;
  background: var(--text-disabled);
  border-radius: 50%;
  transition: all var(--duration-base) var(--ease-spring);
}

.toggle-switch.active {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  border-color: var(--accent);
  box-shadow: var(--shadow-petal-sm);
}

.toggle-switch.active .toggle-slider {
  left: 17px;
  background: var(--text-on-accent);
}

.composer-spoiler-field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.6rem;
  padding: 0.6rem 0.75rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius-md);
  color: var(--accent);
  animation: attach-modal-in var(--duration-base) var(--ease-petal);
}

.composer-spoiler-input {
  flex: 1;
  min-width: 0;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.85rem;
  font-family: inherit;
}

.composer-spoiler-input:focus {
  outline: none;
}

.composer-spoiler-input::placeholder {
  color: var(--text-tertiary);
}

.composer-attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.composer-attachment {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 0.4rem;
  max-width: 220px;
}

.composer-attachment img,
.composer-attachment video {
  width: 72px;
  height: 72px;
  object-fit: cover;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.composer-attachment-anime img {
  width: 44px;
  height: 44px;
}

.composer-attachment-ph {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--accent-subtle);
  color: var(--accent);
  flex-shrink: 0;
}

.composer-attachment-title {
  font-size: 0.8rem;
  color: var(--text-primary);
  line-height: 1.3;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.composer-attachment-remove {
  position: absolute;
  top: -7px;
  right: -7px;
  width: 22px;
  height: 22px;
  min-width: 0;
  min-height: 0;
  padding: 0;
  border: 1px solid var(--border-strong);
  border-radius: 50%;
  background: var(--surface-5);
  color: var(--text-tertiary);
  font-size: 0.75rem;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  transition: all var(--duration-base) var(--ease-petal);
}

.composer-attachment-remove:hover {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
  box-shadow: var(--shadow-petal-sm);
  transform: scale(1.1);
}

.composer-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.composer-body {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.composer-field {
  flex: 1;
  min-height: 40px;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 0.7rem 1rem;
  color: var(--text-primary);
  font-size: 0.95rem;
  font-family: inherit;
  line-height: 1.5;
  resize: none;
  overflow-y: hidden;
  cursor: text;
  transition: all var(--duration-base) var(--ease-petal);
}

.composer-submit {
  flex-shrink: 0;
  align-self: stretch;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.9rem;
  border: none;
  border-radius: 100px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-petal-sm);
  transition: all var(--duration-base) var(--ease-petal);
}

.composer-submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow-sm);
}

.composer-submit:active:not(:disabled) {
  transform: translateY(0);
}

.composer-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.composer-submit :deep(.sakura-icon) {
  color: var(--text-on-accent);
}

.composer-submit:hover :deep(.sakura-icon) {
  color: var(--text-on-accent);
}

/* The composer is one stable two-column layout: avatar + content. */
.composer-card {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  align-items: start;
}

.composer-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: 0.65rem;
  width: 100%;
}

.composer-field {
  grid-column: 1;
}

.composer-submit {
  grid-column: 2;
  min-height: 44px;
  align-self: start;
}

.composer-hashtag-hint,
.composer-actions,
.composer-spoiler-field,
.composer-attachments {
  grid-column: 1 / -1;
  width: 100%;
  margin-top: 0;
  box-sizing: border-box;
}

.composer-spoiler-field {
  min-height: 44px;
  padding: 0.65rem 0.8rem;
}

.composer-spoiler-input {
  min-height: 28px;
}

.composer-error {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-right: auto;
  color: var(--danger);
  font-size: 0.8rem;
}

.composer-action.active {
  color: var(--accent);
  background: var(--accent-subtle);
}

.composer-attachment-body {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.composer-attachment-sub {
  font-size: 0.7rem;
  color: var(--text-tertiary);
}

.composer-attachment-rating {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.7rem;
  color: var(--text-tertiary);
}

.composer-attachment-rating input {
  width: 42px;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
  padding: 0.15rem 0.3rem;
  font-size: 0.75rem;
  text-align: center;
}

.composer-attachment-rating input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent-subtle);
}

/* Attach modal */
.attach-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.attach-modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(5, 4, 8, 0.82);
  backdrop-filter: blur(6px);
}

.attach-modal-content {
  position: relative;
  width: 100%;
  max-width: 560px;
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-modal);
  overflow: hidden;
  animation: attach-modal-in var(--duration-slow) var(--ease-bloom);
}

@keyframes attach-modal-in {
  from {
    opacity: 0;
    transform: translateY(16px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.attach-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-subtle);
}

.attach-modal-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text-primary);
}

.attach-modal-close {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  color: var(--text-tertiary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.attach-modal-close:hover {
  color: var(--danger);
  border-color: var(--danger);
  background: var(--danger-subtle);
}

.attach-modal-tabs {
  display: flex;
  gap: 0.25rem;
  padding: 0.6rem 0.75rem 0;
}

.attach-modal-tabs button {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  background: none;
  border: 1px solid transparent;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  padding: 0.55rem 0.5rem;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.attach-modal-tabs button:hover {
  color: var(--text-secondary);
  background: var(--surface-4);
}

.attach-modal-tabs button.active {
  color: var(--accent);
  background: var(--surface-4);
  border-color: var(--border-default);
  border-bottom-color: var(--accent);
}

.attach-tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: var(--radius-full);
  background: var(--accent);
  color: var(--text-on-accent);
  font-size: 0.68rem;
  font-weight: 700;
}

.attach-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
  min-height: 240px;
}

.attach-tab-content {
  display: flex;
  flex-direction: column;
}

.anime-search-input,
.playlist-search-input {
  width: 100%;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  padding: 0.65rem 0.875rem;
  font-size: var(--text-base);
  font-family: inherit;
  box-sizing: border-box;
  transition: all var(--duration-base) var(--ease-petal);
}

.anime-search-input:focus,
.playlist-search-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

.anime-loading,
.playlist-loading {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  text-align: center;
  padding: 1.25rem;
}

.anime-no-results,
.playlist-no-results {
  color: var(--text-disabled);
  font-size: var(--text-sm);
  text-align: center;
  padding: 1.5rem 0.5rem;
}

.anime-result,
.playlist-result {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.5rem;
  padding: 0.55rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.anime-result:hover,
.playlist-result:hover {
  border-color: var(--accent);
  background: var(--surface-5);
  box-shadow: var(--shadow-petal-sm);
  transform: translateY(-1px);
}

.anime-result img,
.playlist-result img {
  width: 40px;
  height: 56px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}

.anime-result > div,
.playlist-result > div {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.anime-title,
.playlist-title {
  color: var(--text-primary);
  font-size: var(--text-base);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.anime-desc {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.playlist-anime-count {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.check-icon {
  color: var(--accent);
  font-size: 1.05rem;
  font-weight: 700;
  flex-shrink: 0;
}

.media-upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 2.25rem 1rem;
  background: var(--surface-4);
  border: 2px dashed var(--border-strong);
  border-radius: var(--radius-lg);
  cursor: pointer;
  text-align: center;
  transition: all var(--duration-base) var(--ease-petal);
}

.media-upload-area:hover {
  border-color: var(--accent);
  background: var(--accent-subtle);
  box-shadow: var(--shadow-glow-sm);
}

.upload-icon {
  color: var(--accent);
  font-size: 2rem;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.upload-text {
  color: var(--text-secondary);
  font-size: var(--text-md);
  font-weight: 500;
}

.upload-hint {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.hidden-input {
  display: none;
}

.selected-media-preview {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

.selected-media-label {
  color: var(--text-accent);
  font-size: var(--text-sm);
  font-weight: 500;
  margin-bottom: 0.6rem;
}

.media-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(88px, 1fr));
  gap: 0.5rem;
}

.media-preview-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  transition: all var(--duration-base) var(--ease-petal);
}

.media-preview-item:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-petal-sm);
}

.media-preview-item img,
.media-preview-item video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-thumb-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  border: none;
  border-radius: var(--radius-full);
  color: #fff;
  font-size: 0.7rem;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  z-index: 2;
}

.remove-thumb-btn:hover {
  background: var(--danger);
  transform: scale(1.1);
}

.attach-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  padding: 0.875rem 1.25rem;
  border-top: 1px solid var(--border-subtle);
  background: var(--surface-4);
}

.attach-modal-btn-cancel,
.attach-modal-btn-confirm {
  padding: 0.6rem 1.25rem;
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  border: 1px solid var(--border-default);
  background: var(--surface-5);
  color: var(--text-secondary);
}

.attach-modal-btn-cancel:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.attach-modal-btn-confirm {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  border-color: transparent;
  color: var(--text-on-accent);
  box-shadow: var(--shadow-petal-sm);
}

.attach-modal-btn-confirm:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow-sm);
}

@media (max-width: 480px) {
  .composer-card { gap: 10px; }
  .composer-body { flex-basis: 100%; }
  .composer-field { min-height: 72px; }
  .composer-actions { width: 100%; }
  .composer-action { min-height: 44px; }
  .attach-modal {
    padding: 0.5rem;
    align-items: flex-end;
  }
  .attach-modal-content {
    max-height: 92vh;
    border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  }
  .attach-modal-tabs button {
    font-size: var(--text-xs);
  }
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.new-posts-bar {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
  color: white;
  text-align: center;
  padding: 0.75rem;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-weight: 600;
  transition: all var(--duration-base) var(--ease-petal);
  box-shadow: var(--shadow-petal);
}

.new-posts-bar:hover {
  transform: scale(1.02);
  box-shadow: var(--shadow-glow);
}

.load-more {
  text-align: center;
  padding: 1rem;
}

.btn-load-more {
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  padding: 0.75rem 2rem;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-weight: 500;
  transition: all var(--duration-base) var(--ease-petal);
}

.btn-load-more:hover:not(:disabled) {
  background: var(--accent-subtle);
  color: var(--accent);
  border-color: var(--accent);
}

.btn-load-more:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-state {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.skeleton-post {
  background: var(--surface-3);
  border-radius: var(--radius-xl);
  padding: 1.5rem;
}

.skeleton-header {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.skeleton-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--surface-5);
  animation: pulse 1.5s infinite;
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-line {
  height: 12px;
  background: var(--surface-5);
  border-radius: var(--radius-sm);
  animation: pulse 1.5s infinite;
}

.skeleton-line.short {
  width: 40%;
}

.skeleton-line.medium {
  width: 70%;
}

.skeleton-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}

.empty-icon {
  color: var(--text-tertiary);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon :deep(.sakura-icon) {
  color: var(--accent);
  opacity: 0.55;
}

.empty-state h3 {
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: var(--text-tertiary);
  margin-bottom: 1.5rem;
}

.btn-primary {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-lg);
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-petal-sm);
  transition: all var(--duration-base) var(--ease-petal);
}

.btn-primary:hover {
  box-shadow: var(--shadow-glow-sm);
  transform: translateY(-1px);
}

.feed-right-sidebar {
  display: none;
  position: sticky;
  top: 4rem;
  align-self: start;
}

@media (min-width: 900px) {
  .feed-right-sidebar {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
}

.sidebar-card {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1rem;
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-title :deep(.sakura-icon) {
  color: var(--accent);
}

.profile-summary-top {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.profile-summary-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--accent);
  flex-shrink: 0;
}

.profile-summary-info h4 {
  margin: 0;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.profile-summary-username {
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.profile-summary-stats {
  display: flex;
  gap: 1.25rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-subtle);
}

.profile-summary-stats .stat-item {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--accent);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.trending-loading {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.trending-empty {
  color: var(--text-tertiary);
  font-size: 0.85rem;
  text-align: center;
  padding: 0.75rem 0;
}

.trending-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: var(--radius-lg);
  transition: all var(--duration-base) var(--ease-petal);
}

.trending-item:hover {
  background: var(--surface-4);
}

.trend-rank {
  color: var(--accent);
  font-weight: 700;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.trend-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.trend-title {
  color: var(--text-primary);
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trend-stats {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  color: var(--text-tertiary);
  font-size: 0.75rem;
}

/* Subscriptions Tab */
.subscriptions-tab, .not-interested-tab, .reports-tab {
  padding: 1rem 0;
}

.tab-header {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  color: var(--text-primary);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-lg);
  transition: all var(--duration-base) var(--ease-petal);
}

.search-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.subscriptions-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.subscription-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.subscription-card:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-petal-sm);
}

.avatar-lg {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--accent);
}

.subscription-card .user-info {
  flex: 1;
}

.subscription-card h4 {
  color: var(--text-primary);
  margin: 0 0 0.25rem;
  font-size: 1rem;
}

.subscription-card .username {
  color: var(--text-tertiary);
  font-size: 0.85rem;
  display: block;
}

.subscription-card .followers, .subscription-card .hidden-date {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.subscription-card .reason {
  color: var(--danger);
  font-size: 0.8rem;
  display: block;
  margin-top: 0.25rem;
}

.user-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-following {
  background: var(--accent-subtle);
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.85rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.btn-following:hover {
  background: var(--accent);
  color: var(--text-on-accent);
}

.btn-unhide {
  background: var(--danger-subtle);
  color: var(--danger);
  border: 1px solid var(--danger);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  cursor: pointer;
}

.btn-message, .btn-profile {
  background: var(--surface-4);
  color: var(--text-secondary);
  border: none;
  padding: 0.5rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 1.1rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.btn-message:hover, .btn-profile:hover {
  background: var(--accent-subtle);
  color: var(--accent);
}

/* Reports Tab */
.reports-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.report-card {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.report-card:hover {
  border-color: var(--border-default);
}

.report-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.report-type {
  color: var(--accent);
  font-weight: 600;
}

.report-status {
  padding: 0.2rem 0.5rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
}

.report-status.pending {
  background: var(--warning-subtle);
  color: var(--warning);
}

.report-status.resolved {
  background: var(--success-subtle);
  color: var(--success);
}

.report-status.rejected {
  background: var(--danger-subtle);
  color: var(--danger);
}

.report-content p {
  margin: 0.25rem 0;
  color: var(--text-secondary);
}

.report-meta {
  color: var(--text-tertiary);
  font-size: 0.8rem;
  margin-top: 0.5rem;
  display: flex;
  gap: 1rem;
}

.report-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-review {
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.btn-review:hover {
  box-shadow: var(--shadow-glow-sm);
}

.btn-reject {
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.btn-reject:hover {
  background: var(--danger-subtle);
  color: var(--danger);
  border-color: var(--danger);
}

/* Report Detail Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(5,4,8,0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  backdrop-filter: blur(8px);
}

.report-detail-modal {
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-modal);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-subtle);
}

.modal-header h3 {
  color: var(--text-primary);
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-tertiary);
  font-size: 1.25rem;
  cursor: pointer;
  transition: color var(--duration-base) var(--ease-petal);
}

.close-btn:hover {
  color: var(--accent);
}

.modal-body {
  padding: 1.5rem;
}

.report-full-info p {
  margin: 0.5rem 0;
  color: var(--text-secondary);
}

.report-link,
.report-open-link {
  color: var(--accent);
  text-decoration: none;
}

.report-link:hover,
.report-open-link:hover {
  text-decoration: underline;
}

.reported-content {
  margin-top: 1rem;
  padding: 1rem;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--surface-4);
}

.reported-content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.reported-author,
.report-unavailable {
  color: var(--text-tertiary);
}

.reported-content h4 {
  margin: 0.75rem 0 0.35rem;
  color: var(--text-primary);
}

.reported-text {
  margin-top: 0.75rem;
  color: var(--text-secondary);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.reported-media {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.reported-media-item {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.8rem;
}

.reported-media-item img,
.reported-media-item video {
  width: 100%;
  max-height: 220px;
  border-radius: var(--radius-md);
  background: var(--surface-2);
  object-fit: contain;
}

.report-actions-full {
  margin-top: 1.5rem;
}

.report-actions-full label {
  display: block;
  color: var(--text-tertiary);
  margin-bottom: 0.5rem;
}

.action-select {
  width: 100%;
  background: var(--surface-4);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  padding: 0.75rem;
  border-radius: var(--radius-lg);
  margin-bottom: 1rem;
}

.comment-textarea {
  width: 100%;
  background: var(--surface-4);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  padding: 0.75rem;
  border-radius: var(--radius-lg);
  min-height: 100px;
  resize: vertical;
}

.btn-submit {
  width: 100%;
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  padding: 0.75rem;
  border-radius: var(--radius-lg);
  font-weight: 600;
  cursor: pointer;
  margin-top: 1rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.btn-submit:hover {
  box-shadow: var(--shadow-glow-sm);
}

.btn-submit:disabled {
  cursor: wait;
  opacity: 0.65;
}

.report-decision-error {
  margin: 0.75rem 0 0;
  color: var(--danger);
  font-size: 0.875rem;
}

/* Highlight effect for post loaded from route */
.highlight-post {
  animation: highlight-fade 3s ease-out;
}

@keyframes highlight-fade {
  0% {
    box-shadow: 0 0 0 3px var(--accent-glow);
  }
  100% {
    box-shadow: 0 0 0 0 transparent;
  }
}

/* Bookmarks & Pinned tabs */
.bookmarks-tab, .pinned-tab {
  padding: 1rem 0;
}

.pinned-post-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.btn-unpin {
  align-self: flex-end;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  padding: 4px 12px;
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  cursor: pointer;
  font-size: .8rem;
  margin-top: -4px;
  transition: all var(--duration-base) var(--ease-petal);
}

.btn-unpin:hover {
  background: var(--danger-subtle);
  color: var(--danger);
  border-color: var(--danger);
}

/* Attach modal load more */
.anime-load-more {
  display: flex;
  justify-content: center;
  margin-top: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-subtle);
}

.attach-load-more-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.attach-load-more-btn:hover:not(.loading) {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
}

.attach-load-more-btn.loading {
  cursor: default;
  opacity: 0.7;
}

.attach-load-more-btn .spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Trending sidebar */
.trending-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.trending-tabs {
  display: flex;
  gap: 0.25rem;
}

.trending-tab {
  flex: 1;
  padding: 0.35rem 0.5rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.trending-tab:hover {
  color: var(--text-secondary);
  border-color: var(--border-strong);
}

.trending-tab.active {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
}

.trending-skeleton {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border-subtle);
}

.trending-skeleton:last-child {
  border-bottom: none;
}

.trending-skeleton .skeleton-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
  background: linear-gradient(90deg, var(--surface-4) 25%, var(--surface-5) 50%, var(--surface-4) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.trending-skeleton .skeleton-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.trending-skeleton .skeleton-line {
  height: 10px;
  border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-4) 25%, var(--surface-5) 50%, var(--surface-4) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.trending-skeleton .skeleton-line.short {
  width: 60%;
}

.trending-skeleton .skeleton-stats {
  height: 14px;
  width: 80px;
  border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-4) 25%, var(--surface-5) 50%, var(--surface-4) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.trending-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  color: var(--text-tertiary);
  text-align: center;
}

.trending-empty p {
  margin-top: 0.5rem;
  font-size: var(--text-sm);
}

.trending-item {
  display: block;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border-subtle);
  cursor: pointer;
  transition: background var(--duration-base) var(--ease-petal);
}

.trending-item:last-child {
  border-bottom: none;
}

.trending-item:hover {
  background: var(--surface-4);
  padding: 0.75rem;
  margin: 0 -0.25rem;
  border-radius: var(--radius-md);
  border-bottom: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-petal-sm);
}

.trending-item-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.5rem;
}

.trending-author-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.trending-author-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.trending-author-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.trending-author-username {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.trending-time {
  font-size: var(--text-xs);
  color: var(--text-disabled);
  flex-shrink: 0;
}

.trending-item-content {
  margin-bottom: 0.5rem;
}

.trending-text {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0;
}

.trending-anime-badge,
.trending-playlist-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.4rem;
  padding: 0.2rem 0.5rem;
  background: var(--accent-subtle);
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--accent);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trending-media-preview {
  display: flex;
  gap: 0.3rem;
  margin: 0.5rem 0;
  overflow-x: auto;
  padding-bottom: 0.2rem;
}

.trending-media-thumb {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  border: 1px solid var(--border-subtle);
}

.trending-item-stats {
  display: flex;
  gap: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-subtle);
}

.trending-stat {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.25rem 0.5rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.trending-stat:hover {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
}

.trending-stat :deep(.sakura-icon) {
  flex-shrink: 0;
}

.trending-load-more {
  width: 100%;
  margin-top: 0.75rem;
  padding: 0.6rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.trending-load-more:hover:not(:disabled) {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
}

.trending-load-more:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Popular (recommended channels) tab */
.popular-header {
  margin-bottom: 1rem;
}

.popular-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.35rem;
}

.popular-title :deep(.sakura-icon) {
  color: var(--accent);
}

.popular-subtitle {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin: 0;
}

.popular-channels-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.popular-channel-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.popular-channel-item:hover {
  background: var(--surface-4);
  border-color: var(--border-default);
}

.popular-channel-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--accent);
  background: var(--accent-subtle);
  border-radius: var(--radius-sm);
}

/* Matching Channels Section */
.matching-channels-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-subtle);
}

.matching-channels-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.matching-channels-title :deep(.sakura-icon) {
  color: var(--accent);
}

.matching-channels-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.matching-channel-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.matching-channel-item:hover {
  background: var(--surface-4);
  border-color: var(--border-default);
}

.matching-channel-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.matching-channel-rank {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-primary);
  background: var(--surface-4);
  border-radius: var(--radius-full);
}

.matching-channel-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.matching-channel-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.matching-channel-username {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.matching-channel-reasons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.25rem;
}

.matching-reason-tag {
  font-size: var(--text-xs);
  padding: 0.1rem 0.4rem;
  background: var(--accent-subtle);
  color: var(--accent);
  border-radius: var(--radius-sm);
  white-space: nowrap;
}

.matching-channel-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.4rem;
  flex-shrink: 0;
}

.matching-posts-count {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.matching-follow-btn {
  padding: 0.35rem 0.75rem;
  font-size: var(--text-xs);
  font-weight: 600;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  border: 1px solid transparent;
  white-space: nowrap;
}

.matching-follow-btn:not(.following) {
  background: var(--accent);
  color: var(--accent-text);
}

.matching-follow-btn:not(.following):hover {
  filter: brightness(1.1);
}

.matching-follow-btn.following {
  background: transparent;
  color: var(--text-secondary);
  border-color: var(--border-default);
}

.matching-follow-btn.following:hover {
  background: var(--error-subtle);
  color: var(--error);
  border-color: var(--error);
}
</style>
