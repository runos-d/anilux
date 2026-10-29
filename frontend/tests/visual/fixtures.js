const svg = (label, from = "#241440", to = "#8a62bd") =>
  `data:image/svg+xml;charset=utf-8,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="480" height="720"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="${from}"/><stop offset="1" stop-color="${to}"/></linearGradient></defs><rect width="480" height="720" fill="url(#g)"/><circle cx="350" cy="155" r="105" fill="#f4bed5" opacity=".72"/><path d="M50 610c110-185 245-205 380-70v180H50z" fill="#0b0814" opacity=".76"/><text x="240" y="660" text-anchor="middle" fill="#fff" font-family="sans-serif" font-size="25">${label}</text></svg>`)}`;

export const poster = svg("AniLux");

export const user = {
  id: 7,
  username: "sakura_reader",
  nickname: "sakura-reader",
  display_name: "Сакура",
  first_name: "Сакура",
  last_name: "Ханами",
  email: "reader@example.test",
  phone_number: "+7 900 000-00-00",
  avatar: poster,
  avatar_url: poster,
  cover_image: poster,
  bio: "Люблю атмосферные истории, выразительную анимацию и обсуждения после финальных титров.",
  level: 12,
  experience: 640,
  is_online: true,
  email_verified: true,
  phone_verified: true,
  two_factor_enabled: false,
  is_verified: true,
  is_admin: true,
  is_staff: true,
  is_superuser: true,
  followers_count: 128,
  following_count: 64,
  playlists_count: 5,
  created_at: "2025-03-01T10:00:00Z",
  last_login: "2026-01-15T12:00:00Z",
};

export const anime = {
  id: 1,
  anime_id: 1,
  slug: "1-fioletovyy-sad",
  shikimori_id: 1,
  title: "Фиолетовый сад",
  title_ru: "Фиолетовый сад",
  title_en: "Violet Garden",
  title_jp: "Violet Garden",
  description: "История о письмах, памяти и пути к пониманию собственных чувств.",
  poster,
  poster_url: poster,
  poster_image_url: poster,
  screenshots: [svg("Кадр 1", "#15102b", "#7855a2"), svg("Кадр 2", "#24143a", "#ad76bb")],
  year: 2024,
  release_date: "2024-04-05",
  release_date_string: "5 апреля 2024",
  kind: "tv",
  type: "tv",
  status: "ongoing",
  episodes: 12,
  episodes_count: 12,
  score: 8.7,
  rating: 8.7,
  rating_count: 2480,
  genres: ["Драма", "Фэнтези"],
  studios: ["Kyoto Animation"],
  country: "Япония",
  duration: 24,
  age_rating: "PG-13",
  franchise_id: 1,
  franchise_slug: "fioletovyy-sad",
};

export const animeTwo = {
  ...anime,
  id: 2,
  anime_id: 2,
  slug: "2-lunnyy-pochtalon",
  title: "Лунный почтальон",
  title_ru: "Лунный почтальон",
  title_en: "Moon Courier",
  poster: svg("Moon Courier", "#0d1835", "#7457a8"),
  poster_url: svg("Moon Courier", "#0d1835", "#7457a8"),
  poster_image_url: svg("Moon Courier", "#0d1835", "#7457a8"),
  year: 2023,
  status: "finished",
  score: 8.2,
  rating: 8.2,
};

export const animeList = Array.from({ length: 8 }, (_, index) => ({
  ...(index % 2 ? animeTwo : anime),
  id: index + 1,
  anime_id: index + 1,
  slug: `${index + 1}-${index % 2 ? "lunnyy-pochtalon" : "fioletovyy-sad"}`,
  title_ru: index ? `${index % 2 ? "Лунный почтальон" : "Фиолетовый сад"} ${index + 1}` : anime.title_ru,
}));

export const playlist = {
  id: "12345678",
  title: "Тихие истории",
  description: "Подборка атмосферных сериалов для спокойного вечера.",
  visibility: "public",
  privacy: "public",
  cover_image: poster,
  user,
  owner: user,
  author: user,
  items_count: animeList.length,
  likes_count: 38,
  is_liked: false,
  is_favorite: false,
  items: animeList.map((entry, index) => ({ id: index + 1, position: index + 1, anime: entry, note: "" })),
  created_at: "2026-01-01T12:00:00Z",
  updated_at: "2026-01-15T12:00:00Z",
};

export const post = {
  id: 101,
  public_id: 101,
  title: "Впечатления от серии",
  text: "Спокойная публикация о любимой сцене и красивой работе со светом.",
  content: "Спокойная публикация о любимой сцене и красивой работе со светом.",
  author: user,
  author_id: user.id,
  author_name: user.display_name,
  author_username: user.username,
  created_at: "2026-01-15T12:00:00Z",
  published_at: "2026-01-15T12:00:00Z",
  edited_at: null,
  media_files: [],
  attachments: [],
  attachments_data: [{ content_type: "anime", object_id: anime.id, anime_data: anime }],
  comments_count: 4,
  likes_count: 18,
  dislikes_count: 0,
  views_count: 92,
  is_liked: false,
  is_disliked: false,
  is_bookmarked: false,
  is_pinned: false,
  allow_comments: true,
  visibility: "public",
  tags: ["обзор", "атмосфера"],
};

export const comment = {
  id: 401,
  post_id: post.id,
  author: user,
  user,
  content: "Очень точное наблюдение — особенно про работу со светом.",
  text: "Очень точное наблюдение — особенно про работу со светом.",
  created_at: "2026-01-15T12:20:00Z",
  updated_at: "2026-01-15T12:20:00Z",
  likes_count: 3,
  dislikes_count: 0,
  is_liked: false,
  is_disliked: false,
  parent: null,
  parent_id: null,
  replies: [],
};

export const chat = {
  id: 11,
  code: "12345678",
  uuid: "11111111-1111-4111-8111-111111111111",
  type: "group",
  name: "Клуб полуночников",
  title: "Клуб полуночников",
  description: "Обсуждаем новые серии без спойлеров.",
  avatar: poster,
  avatar_url: poster,
  other_user: user,
  members_count: 24,
  unread_count: 3,
  is_owner: true,
  is_admin: true,
  last_message: { id: 301, text: "До встречи после премьеры", sender: user, created_at: "2026-01-15T12:30:00Z" },
};

export const message = {
  id: 301,
  chat_id: chat.id,
  sender: user,
  sender_id: user.id,
  sender_username: user.username,
  text: "Посмотри эту сцену — цвет и композиция получились великолепно.",
  created_at: "2026-01-15T12:30:00Z",
  attachments: [],
  reactions: [],
  is_read: true,
};

const seoPayload = (path) => ({
  title: `Визуальная проверка ${path} | AniLux`,
  description: "Стабильная SEO-проекция для визуальных тестов.",
  h1: "Визуальная проверка",
  canonical: `https://anilux.example${path.split("?")[0]}`,
  robots: "noindex,follow",
  site: "AniLux",
  kind: "utility",
  path: path.split("?")[0],
  status: 200,
  items: animeList.map((entry) => ({ ...entry, name: entry.title_ru, path: `/anime/${entry.slug}`, image: entry.poster_image_url })),
  related: [],
  crumbs: [{ name: "Главная", path: "/" }],
  schema: [],
  contentHtml: '<section class="seo-page"><h1>Визуальная проверка</h1></section>',
});

const calendar = {
  month_key: "2026-01",
  year: 2026,
  month: 1,
  month_label: "Январь 2026",
  today: "2026-01-15",
  grid_start: "2025-12-29",
  grid_end: "2026-02-01",
  has_prev: true,
  has_next: true,
  next_month_key: "2026-02",
  prev_month_key: "2025-12",
  total: 2,
  days: Array.from({ length: 35 }, (_, index) => ({
    date: `2026-01-${String((index % 28) + 1).padStart(2, "0")}`,
    weekday: index % 7,
    weekday_name: ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][index % 7],
    in_month: true,
    is_today: index === 14,
    items: index === 14 ? [{ aired_at: "2026-01-15T18:00:00Z", local_day: "2026-01-15", time: "21:00", episode_number: 5, is_upcoming: true, anime }] : [],
  })),
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
  updated_at: "2026-01-15T12:00:00Z",
};

const idea = {
  id: 1,
  title: "Добавить расписание премьер",
  description: "Показывать ближайшие серии в календаре.",
  kind: "improvement",
  status: "planned",
  priority: "high",
  admin_note: "",
  votes_count: 42,
  is_voted: false,
  is_owner: true,
  author: user.id,
  author_name: user.display_name,
  author_avatar: user.avatar,
  created_at: "2026-01-10T12:00:00Z",
  updated_at: "2026-01-15T12:00:00Z",
};

const watchHistoryItem = {
  anime_id: anime.id,
  slug: anime.slug,
  title: anime.title_ru,
  title_en: anime.title_en,
  poster: anime.poster_image_url,
  year: anime.year,
  kind: anime.kind,
  kind_label: "Сериал",
  score: anime.score,
  genres: anime.genres,
  season_number: 1,
  episode: 4,
  continue_season: 1,
  continue_episode: 4,
  total_episodes: anime.episodes,
  watched_episodes: 3,
  episode_status: "in_progress",
  position: 612,
  duration: 1440,
  episode_percent: 43,
  series_percent: 29,
  last_watched: "2026-01-15T12:00:00Z",
  is_series_completed: false,
};

const excerpt = {
  id: 1,
  anime_id: anime.id,
  anime_title: anime.title_ru,
  poster_url: anime.poster_image_url,
  season: 1,
  episode: 4,
  translation_id: 77,
  translation_title: "AniLibria",
  player_link: "https://kodikplayer.com/seria/visual-test/720p",
  duration: 1440,
  start: 318.25,
  end: 346.8,
  title: "Тихая сцена",
  description: "Короткий фрагмент для визуальной проверки.",
  shared: true,
  share_path: "/excerpts/s/visualtoken",
  unavailable: false,
};

const achievement = { id: 1, title: "Первый просмотр", name: "Первый просмотр", description: "Просмотрен первый эпизод", icon: "star", unlocked: true, progress: 1, target: 1 };

const json = (route, body, status = 200) => route.fulfill({
  status,
  contentType: "application/json; charset=utf-8",
  body: JSON.stringify(body),
});

const mediaPlaceholder = `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="480" viewBox="0 0 480 480">
  <defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#171024"/><stop offset="1" stop-color="#7654a3"/></linearGradient></defs>
  <rect width="480" height="480" fill="url(#g)"/><circle cx="240" cy="188" r="82" fill="#f4bed5" opacity=".78"/>
  <path d="M92 446c20-100 76-150 148-150s128 50 148 150" fill="#0b0814" opacity=".72"/>
</svg>`;

export async function installVisualApi(page, theme) {
  await page.route("https://fonts.googleapis.com/**", (route) => route.fulfill({
    status: 200,
    contentType: "text/css; charset=utf-8",
    body: "/* Visual tests use the checked-in system font fallback. */",
  }));
  await page.route("https://fonts.gstatic.com/**", (route) => route.fulfill({ status: 204, body: "" }));
  await page.route("https://kodikplayer.com/**", (route) => route.fulfill({
    status: 200,
    contentType: "text/html; charset=utf-8",
    body: '<!doctype html><html><body style="margin:0;background:#08060d;color:#d8cee9;display:grid;place-items:center;height:100vh;font:14px system-ui">Стабильная область видеоплеера</body></html>',
  }));
  const fulfillMedia = (route) => route.fulfill({
    status: 200,
    contentType: "image/svg+xml; charset=utf-8",
    body: mediaPlaceholder,
  });
  await page.route("**/data/media/**", fulfillMedia);
  await page.route("**/media/**", fulfillMedia);
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (!url.pathname.startsWith("/api/")) {
      await route.continue();
      return;
    }
    const path = url.pathname.replace(/^\/api/, "");

    if (path === "/seo/page/") return json(route, seoPayload(url.searchParams.get("path") || "/"));
    if (["/users/profile/", "/users/me/"].includes(path)) return json(route, user);
    if (path.includes("/token/refresh/")) return json(route, { access: "visual-access", refresh: "visual-refresh" });
    if (path === "/users/theme-settings/") return json(route, {
      theme,
      theme_accents: {},
      custom_theme: {},
      use_shared_background: true,
      custom_background: "default",
      font_family: "system",
      font_size: 14,
      line_spacing: 1.5,
      font_weight: "normal",
      smooth_animations: false,
      scroll_effects: false,
      parallax_effect: false,
      truncate_names: true,
      compact_lists: true,
      hide_avatars: false,
      show_time_everywhere: false,
      small_emojis: true,
      high_contrast: false,
      sakura_enabled: false,
      new_year_enabled: false,
      halloween_enabled: false,
      love_day_enabled: false,
    });
    if (path === "/users/settings/" || path === "/settings/") return json(route, { theme, language: "ru", notifications_enabled: true, privacy: {} });
    if (path === "/users/sessions/active/") return json(route, [{ id: 1, session_key: "visual-session", device_name: "Chrome", is_current_device: true, location: "", last_activity: "2026-10-28T10:00:00Z" }]);
    if (path === "/users/storage-usage/") return json(route, { used: 1024, total: 1024, limit: 2147483648, media: 1024, documents: 0, audio: 0, messages: 0, cache: 0, breakdown: {} });
    if (path === "/users/library/check_anime/") return json(route, { in_library: true, status: libraryItem.status, item: libraryItem });
    if (path === "/users/sessions/") return json(route, [{ id: 1, device: "Chrome", location: "Москва", current: true, last_activity: "2026-01-15T12:00:00Z" }]);
    if (path.includes("/users/library/statistics")) return json(route, { total: 42, completed: 28, watching: 6, planned: 8, hours_watched: 280, favorite_genres: ["Драма", "Фэнтези"] });
    if (path.includes("/users/library/wrapped")) return json(route, { year: 2025, total_anime: 42, total_episodes: 630, hours: 280, top_genres: ["Драма", "Фэнтези"], top_anime: animeList.slice(0, 3) });
    if (path === "/users/library/" || path.startsWith("/users/library/?")) return json(route, { results: [libraryItem], count: 1, total_count: 1, page: 1, page_size: 20, total_pages: 1 });
    if (path.startsWith("/users/users/") || path.startsWith("/users/search") || path.startsWith("/users/online")) return json(route, { results: [user], count: 1 });

    if (path === "/anime/home/") {
      const recommendations = animeList.map((entry) => ({ anime_id: entry.id, slug: entry.slug, title: entry.title_ru, poster: entry.poster_image_url, rating: entry.score, rating_count: 120, year: entry.year, kind: entry.kind, status: entry.status, episodes: entry.episodes, genres: entry.genres }));
      return json(route, { trending: recommendations, recommendations, continue_watching: [{ ...recommendations[0], current_episode: 4 }], rewatch: [], new_episodes: [{ ...recommendations[1], latest_episode: 7, next_episode: 7, unwatched_count: 2 }] });
    }
    if (path === "/anime/home/personalized/") return json(route, { top_rated: animeList, new_season: animeList.slice(0, 4), based_on_watched: animeList.slice(2), classics: animeList, short: animeList, movies: animeList });
    if (path === "/anime/calendar/") return json(route, calendar);
    if (path === "/anime/excerpts/") return json(route, { results: [excerpt], count: 1, next: null });
    if (/^\/anime\/excerpts\/shared\/[^/]+\/$/.test(path)) return json(route, excerpt);
    if (/^\/anime\/excerpts\/\d+\/$/.test(path)) return json(route, excerpt);
    if (path === "/anime/genres/") return json(route, ["Драма", "Фэнтези", "Романтика", "Повседневность"]);
    if (path === "/anime/types/") return json(route, ["tv", "movie", "ova", "ona"]);
    if (path === "/anime/catalog-settings/") return json(route, { group_franchises: true });
    if (path === "/anime/random/") return json(route, animeList);
    if (path === "/anime/search/") return json(route, { query: url.searchParams.get("q") || "", results: animeList, total: animeList.length, page: 1, page_size: 20, has_more: false, source: "fixtures" });
    if (path === "/anime/announcements/") return json(route, { results: animeList.slice(0, 3), count: 3, page: 1, page_size: 20, total_pages: 1 });
    if (path === "/anime/" || path === "/anime/anime/") return json(route, { results: animeList, count: animeList.length, total_count: animeList.length, page: 1, page_size: 50, total_pages: 1 });
    if (/^\/anime\/franchises\//.test(path)) return json(route, { id: 1, slug: "fioletovyy-sad", name: "Фиолетовый сад", title: "Фиолетовый сад", description: "Все части в порядке просмотра.", poster_image_url: poster, entries: animeList.slice(0, 3), anime: animeList.slice(0, 3), parts: animeList.slice(0, 3) });
    if (/^\/anime\/announcements\//.test(path)) return json(route, { ...anime, id: 51, slug: "novaya-istoriya", title_ru: "Новая история", release_date: "2026-04-01", studio: "Ani Studio" });
    if (/^\/anime\/\d+\/episodes\//.test(path)) return json(route, animeList.slice(0, 6).map((_, index) => ({ id: index + 1, episode_number: index + 1, title: `Серия ${index + 1}`, duration: 1440 })));
    if (/^\/anime\/\d+\/(?:translations|kodik_translations|custom_dubs|alternative_streams|episode-notifications)\//.test(path)) return json(route, []);
    if (path === "/anime/watch-history/") return json(route, {
      results: [watchHistoryItem],
      count: 1,
      next: null,
      previous: null,
      summary: { total: 1, in_progress: 1, watched: 0 },
    });
    if (/^\/anime\/[^/]+\/$/.test(path)) return json(route, anime);

    if (path.startsWith("/playlists/playlists/discovery-options")) return json(route, { topics: [{ id: 1, name: "Атмосферные" }], genres: ["Драма", "Фэнтези"] });
    if (path.startsWith("/playlists/playlists/counts")) return json(route, { all: 4, my: 2, favorites: 1, public: 4 });
    if (path.startsWith("/playlists/playlists/shared/")) return json(route, playlist);
    if (/^\/playlists\/playlists\/\d+\/$/.test(path)) return json(route, playlist);
    if (path.startsWith("/playlists/playlists/my")) return json(route, { results: [playlist], count: 1, next: null, previous: null });
    if (path === "/playlists/playlists/" || path.startsWith("/playlists/playlists/?")) return json(route, { results: [playlist], count: 1, next: null, previous: null });
    if (path.startsWith("/playlists/favorites")) return json(route, { results: [], count: 0, anime_ids: [] });

    if (path === "/social/feed/extended/" || path === "/social/feed/weighted/" || path === "/social/posts/") return json(route, { results: [post], count: 1, next: null, previous: null });
    if (/^\/social\/posts\/\d+\/comments\/$/.test(path)) return json(route, [comment]);
    if (/^\/social\/posts\/\d+\/$/.test(path)) return json(route, post);
    if (path === "/social/news/") return json(route, [{ ...post, id: 201, title: "Обновление AniLux", image: poster }]);
    if (path === "/social/chats/unread-count/") return json(route, { unread_count: 3 });
    if (path === "/social/chats/unread/") return json(route, { results: [{ ...chat, unread_count: 3 }] });
    if (path.startsWith("/social/private-chats") || path === "/social/group-chats/" || path.startsWith("/social/chats/for-forward")) return json(route, [chat]);
    if (/^\/social\/(?:chats|private-chats|group-chats)\//.test(path) && path.endsWith("/messages/")) return json(route, { results: [message], count: 1, next: null, previous: null });
    if (/^\/social\/(?:chats|private-chats|group-chats)\//.test(path)) return json(route, chat);
    if (path.startsWith("/social/chat-settings")) return json(route, { accent_color: "#9b7bd4", wallpaper_type: "solid", wallpaper_color: "#0f0b1a", notifications_enabled: true });
    if (path === "/social/chat-folders/") return json(route, [{ id: 1, name: "Избранные", color: "#9b7bd4", chats: [chat] }]);
    if (path === "/social/complaints/") return json(route, [{ id: 1, reason: "Проверка", status: "pending", reporter: user, created_at: "2026-01-15T12:00:00Z" }]);

    if (path === "/ideas/") return json(route, { results: [idea], count: 1, next: null, previous: null });
    if (path.startsWith("/notifications/notifications/count")) return json(route, { count: 3, unread_count: 3 });
    if (path.startsWith("/notifications/notifications")) return json(route, { results: [{ id: 1, title: "Новая серия", content: "Доступна пятая серия", type: "anime", is_read: false, created_at: "2026-01-15T12:00:00Z" }], count: 1 });
    if (path === "/notifications/settings/") return json(route, { push_enabled: true, email_enabled: false, type_settings: {} });
    if (path.startsWith("/notifications/reminders")) return json(route, []);
    if (path.startsWith("/social/achievements") || path.startsWith("/social/admin/achievements")) return json(route, [achievement]);

    if (path === "/dubs/people/") return json(route, { results: [{ id: 1, name: "Акира Хоси", slug: "akira-hoshi", photo: poster, roles: ["Сэйю"] }], count: 1 });
    if (path.startsWith("/dubs/people/")) return json(route, { id: 1, name: "Акира Хоси", slug: "akira-hoshi", photo: poster, description: "Актёр озвучивания.", anime: animeList.slice(0, 3) });
    if (path.startsWith("/admin/import-status")) return json(route, { running: false, finished: true, success: true, log: "Импорт завершён" });
    if (path.startsWith("/anime/admin/franchises")) return json(route, { results: [{ id: 1, name: "Фиолетовый сад", slug: "fioletovyy-sad", entries_count: 3 }], count: 1 });

    if (request.method() !== "GET") return json(route, { ok: true, success: true, message: "Fixture action completed" });
    return json(route, { results: [], items: [], count: 0, total: 0, next: null, previous: null });
  });
}

export async function installVisualSession(page, theme, consentState = "denied") {
  await page.addInitScript(({ currentTheme, currentUser, currentConsentState }) => {
    const legacyTheme = currentTheme === "light" ? "light" : "dark";
    localStorage.setItem("appearance:v1", JSON.stringify({ s: { theme: currentTheme, smoothAnimations: false, sakuraEnabled: false }, o: {} }));
    localStorage.setItem("userSettings", JSON.stringify({ theme: legacyTheme, ui_style: "modern", text_size: "medium" }));
    localStorage.setItem("currentSettings", JSON.stringify({ theme: legacyTheme, textSize: "medium", uiStyle: "modern" }));
    localStorage.setItem("anilux_access_token_v1", "visual-access");
    localStorage.setItem("anilux_refresh_token_v1", "visual-refresh");
    localStorage.setItem("anilux_user_v1", JSON.stringify(currentUser));
    if (currentConsentState === "unknown") localStorage.removeItem("anilux.analytics.consent");
    else localStorage.setItem("anilux.analytics.consent", JSON.stringify({
      state: currentConsentState,
      policyVersion: "2026-10-27.1",
      decidedAt: "2026-10-27T00:00:00.000Z",
      source: "banner",
    }));
    class VisualWebSocket {
      static OPEN = 1;
      readyState = 1;
      addEventListener() {}
      removeEventListener() {}
      send() {}
      close() {}
    }
    Object.defineProperty(window, "WebSocket", { value: VisualWebSocket, configurable: true });
  }, { currentTheme: theme, currentUser: user, currentConsentState: consentState });
  await installVisualApi(page, theme);
}
