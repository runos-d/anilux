<template>
  <div class="playlist-detail">
    <div class="playlist-header">
      <div v-if="playlist.cover_urls?.original" class="playlist-cover">
        <img :src="playlist.cover_urls.original" :alt="playlist.title" />
      </div>

      <div class="playlist-info">
        <h1>{{ playlist.title }}</h1>
        <p v-if="playlist.description" class="description">
          {{ playlist.description }}
        </p>

        <div class="playlist-meta">
          <span v-if="playlist.user"
            ><SakuraIcon name="user" /> {{ playlist.user.username }}</span
          >
          <span
            ><SakuraIcon name="chart" />
            {{ playlist.items_count || playlist.items?.length || 0 }} аниме</span
          >
          <span
            ><SakuraIcon name="heart" /> {{ playlist.favorites_count || 0 }} в
            избранном</span
          >
        </div>

        <div class="playlist-actions" v-if="currentUserId">
          <button
            @click="$emit('toggle-favorite', playlist)"
            :class="[
              'action-btn',
              'favorite-btn',
              { active: playlist.is_favorited },
            ]"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
              />
            </svg>
            {{ playlist.is_favorited ? "В избранном" : "В избранное" }}
          </button>

          <button @click="$emit('duplicate', playlist)" class="action-btn">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path
                d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
              />
            </svg>
            Копировать
          </button>

          <template v-if="currentUserId === playlist.user_id">
            <button
              @click="$emit('add-anime', playlist)"
              class="action-btn primary"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M12 5v14M5 12h14" />
              </svg>
              Добавить аниме
            </button>

            <button @click="$emit('edit', playlist)" class="action-btn">
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
              Редактировать
            </button>

            <button @click="$emit('delete', playlist)" class="action-btn danger">
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

            <button
              @click="$emit('toggle-privacy', playlist)"
              class="action-btn"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              {{
                playlist.is_public ? "Сделать приватным" : "Сделать публичным"
              }}
            </button>

            <button @click="$emit('update-cover', playlist)" class="action-btn">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
              Обновить обложку
            </button>
          </template>
        </div>
      </div>
    </div>

    <div v-if="playlist.items && playlist.items.length > 0" class="playlist-items">
      <h2>Аниме в плейлисте</h2>
      <div class="items-list">
        <div v-for="item in playlist.items" :key="item.id" class="playlist-item">
          <img
            v-if="item.anime?.poster_image_url"
            :src="item.anime.poster_image_url"
            :alt="item.anime.title_ru || item.anime.title_en"
            class="item-poster"
          />
          <div class="item-info">
            <h3>{{ item.anime?.title_ru || item.anime?.title_en }}</h3>
            <p v-if="item.notes" class="item-notes">{{ item.notes }}</p>
          </div>
          <div class="item-position">#{{ (item.position ?? 0) + 1 }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Playlist {
  id: number | string;
  title: string;
  description?: string;
  user_id: number;
  user?: {
    id: number;
    username: string;
  };
  items_count?: number;
  items?: Array<{
    id: number;
    anime: {
      poster_image_url?: string;
      title_ru?: string;
      title_en?: string;
    };
    notes?: string;
    position?: number;
  }>;
  favorites_count?: number;
  is_favorited?: boolean;
  is_public?: boolean;
  cover_urls?: {
    original?: string;
    thumbnail?: string;
  };
}

interface Props {
  playlist: Playlist;
  currentUserId?: number;
}

defineProps<Props>();

defineEmits<{
  "toggle-favorite": [playlist: Playlist];
  duplicate: [playlist: Playlist];
  "add-anime": [playlist: Playlist];
  edit: [playlist: Playlist];
  delete: [playlist: Playlist];
  "update-cover": [playlist: Playlist];
  "toggle-privacy": [playlist: Playlist];
  "item-notes-change": [item: unknown];
  reorder: [items: unknown[]];
}>();
</script>

<style scoped>
.playlist-detail {
  background: var(--surface-3);
  border-radius: 1rem;
  overflow: hidden;
}

.playlist-header {
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-default);
}

.playlist-cover {
  width: 200px;
  height: 200px;
  flex-shrink: 0;
  border-radius: 0.75rem;
  overflow: hidden;
  background: var(--surface-2);
}

.playlist-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.playlist-info {
  flex: 1;
  min-width: 0;
}

.playlist-info h1 {
  margin: 0 0 0.5rem 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
}

.description {
  color: var(--text-secondary);
  margin: 0 0 1rem 0;
  line-height: 1.6;
}

.playlist-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.playlist-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: var(--surface-1);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--surface-1-hover);
}

.action-btn.primary {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.action-btn.primary:hover {
  background: var(--accent-dark);
}

.action-btn.danger {
  background: rgba(220, 38, 38, 0.1);
  color: #dc2626;
  border-color: rgba(220, 38, 38, 0.3);
}

.action-btn.danger:hover {
  background: rgba(220, 38, 38, 0.2);
}

.action-btn.favorite-btn.active {
  color: var(--accent-3);
  background: rgba(255, 42, 109, 0.1);
  border-color: rgba(255, 42, 109, 0.3);
}

.playlist-items {
  padding: 1.5rem;
}

.playlist-items h2 {
  margin: 0 0 1rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.playlist-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--surface-1);
  border-radius: 0.5rem;
  transition: background 0.2s;
}

.playlist-item:hover {
  background: var(--surface-1-hover);
}

.item-poster {
  width: 60px;
  height: 90px;
  object-fit: cover;
  border-radius: 0.375rem;
  flex-shrink: 0;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-info h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.item-notes {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.item-position {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .playlist-header {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .playlist-cover {
    width: 100%;
    height: 200px;
  }

  .playlist-info h1 {
    font-size: 1.375rem;
  }

  .playlist-items {
    padding: 1rem;
  }

  .item-poster {
    width: 50px;
    height: 75px;
  }
}

@media (max-width: 480px) {
  .playlist-header {
    padding: 0.875rem;
  }

  .playlist-cover {
    height: 160px;
  }

  .playlist-info h1 {
    font-size: 1.2rem;
  }

  .playlist-meta {
    font-size: 0.8125rem;
    gap: 0.75rem;
  }

  .action-btn {
    padding: 0.4375rem 0.75rem;
    font-size: 0.8125rem;
  }

  .playlist-items {
    padding: 0.875rem;
  }

  .playlist-items h2 {
    font-size: 1.1rem;
  }

  .playlist-item {
    gap: 0.75rem;
    padding: 0.625rem;
  }

  .item-info h3 {
    font-size: 0.9375rem;
  }

  .item-notes {
    font-size: 0.8125rem;
  }

  .item-position {
    font-size: 0.8125rem;
  }
}
</style>