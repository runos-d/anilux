<template>
  <main class="visual-gallery" data-visual-gallery>
    <header class="visual-gallery__header">
      <p>Argos component harness</p>
      <h1>{{ selectedLabel || "Все модальные окна" }}</h1>
    </header>

    <section v-if="!selectedComponent" class="visual-gallery__index">
      <a
        v-for="entry in entries"
        :key="entry.key"
        :href="`/__visual__/modals?name=${encodeURIComponent(entry.key)}`"
        :data-modal-key="entry.key"
      >
        {{ entry.label }}
      </a>
    </section>

    <section v-else class="visual-gallery__stage" :data-modal-name="selectedLabel">
      <Suspense>
        <component :is="selectedComponent" v-bind="fixtureProps">
          <div class="visual-gallery__slot">
            <strong>Содержимое модального окна</strong>
            <p>Фиксированное состояние для визуального тестирования.</p>
          </div>
          <template #footer>
            <button type="button">Отмена</button>
            <button type="button">Сохранить</button>
          </template>
        </component>
        <template #fallback><div class="visual-gallery__loading">Загрузка компонента…</div></template>
      </Suspense>
      <p class="visual-gallery__empty">
        Если окно не появилось поверх этой подписи, компонент не отрисовывает переданное открытое состояние.
      </p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const loaders = {
  ...import.meta.glob("../components/**/*Modal.vue"),
  ...import.meta.glob("../components/**/*Dialog.vue"),
};

const entries = Object.entries(loaders)
  .map(([key, loader]) => ({
    key,
    label: key.replace("../components/", "").replace(/\.vue$/, ""),
    loader,
  }))
  .sort((a, b) => a.label.localeCompare(b.label, "ru"));

const selectedKey = computed(() => String(route.query.name || ""));
const selected = computed(() => entries.find((entry) => entry.key === selectedKey.value));
const selectedLabel = computed(() => selected.value?.label || "");
const selectedComponent = computed(() => selected.value ? defineAsyncComponent(selected.value.loader as never) : null);

const pixel =
  "data:image/svg+xml;charset=utf-8," +
  encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="720"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#21143c"/><stop offset="1" stop-color="#7651a8"/></linearGradient></defs><rect width="480" height="720" fill="url(#g)"/><circle cx="360" cy="150" r="95" fill="#f4b8d0" opacity=".75"/><path d="M70 590c95-180 210-205 340-70v200H70z" fill="#0d0918" opacity=".75"/></svg>');

const anime = {
  id: 1,
  anime_id: 1,
  slug: "1-fioletovyy-sad",
  title: "Фиолетовый сад",
  title_ru: "Фиолетовый сад",
  title_en: "Violet Garden",
  title_jp: "Violet Garden",
  poster: pixel,
  poster_url: pixel,
  poster_image_url: pixel,
  description: "История о письмах, памяти и пути к пониманию собственных чувств.",
  year: 2024,
  kind: "tv",
  type: "tv",
  status: "ongoing",
  episodes: 12,
  episodes_count: 12,
  score: 8.7,
  rating: 8.7,
  genres: ["Драма", "Фэнтези"],
};

const user = {
  id: 7,
  user_id: 7,
  username: "sakura_reader",
  nickname: "sakura-reader",
  display_name: "Сакура",
  email: "reader@example.test",
  avatar: pixel,
  avatar_url: pixel,
  level: 12,
  experience: 640,
  is_online: true,
  is_verified: true,
  is_admin: true,
  is_staff: true,
  is_superuser: true,
};

const post = {
  id: 101,
  public_id: 101,
  author: user,
  author_id: user.id,
  author_name: user.display_name,
  author_username: user.username,
  text: "Спокойная публикация о любимой сцене и красивой работе со светом.",
  title: "Впечатления от серии",
  created_at: "2026-01-15T12:00:00Z",
  published_at: "2026-01-15T12:00:00Z",
  media_files: [],
  attachments_data: [],
  comments_count: 4,
  likes_count: 18,
  dislikes_count: 0,
  is_liked: false,
  is_bookmarked: false,
};

const playlist = {
  id: "12345678",
  title: "Тихие истории",
  description: "Подборка атмосферных сериалов для спокойного вечера.",
  visibility: "public",
  privacy: "public",
  cover_image: pixel,
  user,
  owner: user,
  items_count: 6,
  items: [{ id: 1, position: 1, anime }],
};

const message = {
  id: 301,
  chat_id: 11,
  sender: user,
  sender_id: user.id,
  sender_username: user.username,
  text: "Посмотри эту сцену — цвет и композиция получились великолепно.",
  created_at: "2026-01-15T12:30:00Z",
  attachments: [],
};

const chat = {
  id: 11,
  code: "12345678",
  type: "group",
  name: "Клуб полуночников",
  title: "Клуб полуночников",
  avatar: pixel,
  members_count: 24,
  unread_count: 3,
};

const libraryItem = {
  id: 501,
  anime,
  anime_id: anime.id,
  status: "started",
  current_episode: 4,
  rating: 8,
  notes: "Продолжить на выходных",
  is_favorite: true,
};

const fixtureProps = {
  show: true,
  modelValue: true,
  isOpen: true,
  isVisible: true,
  open: true,
  title: "Проверка модального окна",
  message: "Действие изменит сохранённые настройки. Проверьте детали перед продолжением.",
  anime,
  animeId: anime.id,
  animeTitle: anime.title_ru,
  animePoster: pixel,
  totalEpisodes: 12,
  currentSeason: 1,
  currentEpisode: 4,
  episodeGroups: [{ season: 1, title: "Сезон 1", episodes: Array.from({ length: 12 }, (_, index) => ({ id: index + 1, episode: index + 1, title: `Серия ${index + 1}` })) }],
  user,
  users: [user, { ...user, id: 8, username: "moonlight", display_name: "Луна" }],
  achievements: [{ id: 1, title: "Первый просмотр", name: "Первый просмотр", description: "Просмотрен первый эпизод", icon: "star", category: "basic", progress: 1, max_progress: 1, unlocked_at: "2026-01-15T12:00:00Z" }],
  stats: {
    profile_views: 1280,
    unique_visitors: 740,
    weekly_views: [82, 116, 94, 151, 173, 208, 190],
    new_followers: 18,
    unfollowed_count: 2,
    total_followers: 128,
    post_likes: 386,
    comments: 94,
    reposts: 31,
    popular_content: [{ id: 101, title: "Впечатления от серии", views: 920, likes: 86 }],
  },
  post,
  contentType: "post",
  contentId: post.id,
  targetId: anime.id,
  targetType: "anime",
  targetName: anime.title_ru,
  playlist,
  playlistId: Number(playlist.id),
  playlistLink: "https://example.test/playlist/12345678",
  playlists: [playlist],
  item: libraryItem,
  selectedAnimes: [anime],
  selectedPlaylists: [playlist],
  selectedMediaFiles: [],
  selectedExcerpts: [],
  images: [pixel, pixel],
  imageUrl: pixel,
  initialSrc: pixel,
  phone: "+7 900 000-00-00",
  email: user.email,
  chatId: chat.id,
  chatType: "group",
  chatName: chat.name,
  chatAvatar: pixel,
  isGroup: true,
  isAdmin: true,
  isOwner: true,
  chats: [chat],
  availableChats: [chat, { ...chat, id: 12, name: "Обсуждение сезона" }],
  selectedChat: chat,
  folder: { id: 1, name: "Избранные", color: "#9b7bd4", icon: "star", chats: [chat] },
  member: { id: 1, role: "member", user },
  existingInvite: { id: 1, invite_link: "visual-test-link", expires_at: "2026-12-31T00:00:00Z", usage_count: 2, usage_limit: 10 },
  onClose: () => undefined,
  onSave: () => undefined,
};
</script>

<style scoped>
.visual-gallery {
  min-height: 100vh;
  padding: 32px;
  color: var(--text-primary);
  background: var(--surface-1);
}

.visual-gallery__header {
  position: relative;
  z-index: 1;
  max-width: 1100px;
  margin: 0 auto 24px;
}

.visual-gallery__header p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  letter-spacing: .12em;
  text-transform: uppercase;
}

.visual-gallery__header h1 { margin: 6px 0 0; font-size: 24px; }
.visual-gallery__index { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; max-width: 1100px; margin: auto; }
.visual-gallery__index a { padding: 12px 14px; border: 1px solid var(--border-default); border-radius: var(--radius-md); color: var(--text-primary); background: var(--surface-2); text-decoration: none; }
.visual-gallery__stage { min-height: 75vh; display: grid; place-items: center; }
.visual-gallery__empty { max-width: 560px; padding: 18px; border: 1px dashed var(--border-default); border-radius: var(--radius-lg); color: var(--text-secondary); text-align: center; }
.visual-gallery__loading { color: var(--text-secondary); }
.visual-gallery__slot { padding: 20px; }
</style>
