---
id: docs-manifest
title: Манифест разделов документации и watch paths
status: draft
date: '2026-10-11'
tags:
- knowledge-management
- documentation
kind: derived
governed-by: TBD
last-verified:
kms-generated: true
---

Исходные документы и новый AGENTS.md; знания docs/{facts,decisions,guardrails,skills} покрываются своими INDEX.md. Каждый раздел наследует watch на сам файл документа и использует наборы ниже. last-verified пустой: это mapping bootstrap, не проверка истинности документа. IDs обозначают draft intent-кандидатов, внешние API-справочники не считаются принятыми решениями AniSphere.

## Наборы watch paths

- `W-kms`: `AGENTS.md`; `.gitignore`; `docs/facts/**`; `docs/decisions/**`; `docs/guardrails/**`; `docs/skills/**`
- `W-runtime`: `backend/requirements.txt`; `backend/Dockerfile`; `frontend/package.json`; `frontend/package-lock.json`; `frontend/Dockerfile`
- `W-env`: `docker-compose*.yml`; `backend/config/settings*.py`; `frontend/vite.config.ts`
- `W-release`: `docker-compose*.yml`; `backend/docker_entrypoint.py`; `backend/core/project_schema.py`; `frontend/nginx.conf`; `scripts/*backup.py`; `scripts/*rehearsal.py`
- `W-checks`: `frontend/package.json`; `frontend/vitest.config.ts`; `frontend/src/**/*.test.ts`; `frontend/tests/**`; `backend/apps/**/test*.py`; `backend/config/settings*test.py`; `backend/config/settings*integration.py`; `scripts/profile_local_chats.mjs`
- `W-anime`: `backend/apps/anime/**`; `frontend/src/api/anime*`; `frontend/src/components/page/anime/**`; `frontend/src/composables/useAnime*.ts`
- `W-seo`: `backend/apps/seo/**`; `backend/config/urls.py`; `frontend/nginx.conf`; `frontend/src/entry.ts`; `frontend/src/lib/seo*.ts`; `frontend/src/composables/useSeo*`; `frontend/tests/seo-browser.js`; `scripts/*seo*.py`; `docker-compose*.yml`
- `W-kodik`: `backend/apps/anime/infrastructure/clients/kodik*`; `backend/apps/anime/application/*kodik*`; `backend/apps/anime/management/commands/*kodik*`; `frontend/src/components/Players/**`; `backend/config/celery.py`
- `W-shikimori`: `backend/apps/anime/infrastructure/clients/**`; `backend/apps/anime/application/**`
- `W-chat`: `backend/apps/social/**`; `frontend/src/api/chat*.ts`; `frontend/src/api/chats.ts`; `frontend/src/stores/*Chat.ts`; `frontend/src/stores/chat*.ts`; `frontend/src/components/Chats/**`; `frontend/src/components/page/chats/**`; `frontend/src/components/modal/chats/**`; `frontend/src/lib/chat*.ts`; `frontend/src/lib/discussionMembership*`; `frontend/src/lib/privateMediaCache*`; `frontend/src/composables/useChat*.ts`; `frontend/src/composables/useGlobalWebSocket.ts`; `frontend/src/sw.ts`; `frontend/tests/chat-*.js`
- `W-post`: `backend/apps/social/**`; `frontend/src/api/feed.ts`; `frontend/src/stores/posts.ts`; `frontend/src/components/feed/**`; `frontend/src/components/page/feed/**`; `frontend/src/components/modal/feed/**`; `frontend/src/lib/post*.ts`; `frontend/tests/site-*.js`
- `W-notif`: `backend/apps/notifications/**`; `backend/apps/users/**`; `backend/apps/social/application/chat_notification_preferences.py`; `backend/config/celery.py`; `frontend/src/stores/notifications.ts`; `frontend/src/components/*otifications/**`; `frontend/src/components/settings/NotificationsSettings.vue`; `frontend/src/composables/useTabBadge*`; `frontend/src/lib/browserNotifications*`; `frontend/src/lib/chatNotificationPreferences*`; `frontend/src/sw.ts`
- `W-seo`: `backend/apps/anime/presentation/**`; `backend/seo_templates.md`; `frontend/src/composables/useSeo.ts`; `frontend/src/router/index.ts`; `frontend/public/robots.txt`; `frontend/public/sitemap*`; `frontend/index.html`
- `W-avatars`: `frontend/src/assets/translation-avatars/**`; `frontend/src/utils/translationAvatars.ts`; `frontend/src/components/Dubs/**`; `frontend/src/components/page/anime/AnimeDetailView.vue`; `frontend/src/components/page/anime/AnimeWatchView.vue`
- `W-default-avatars`: `frontend/public/def_ava/**`; `frontend/src/utils/defaultAvatars.ts`; `backend/apps/users/**`
- `W-favorites`: `backend/apps/anime/**`; `backend/apps/playlists/**`; `backend/apps/users/**`; `backend/apps/social/**`; `frontend/src/components/page/other/FavoritesView.vue`; `frontend/src/components/page/profile/UserLibraryView.vue`
- `W-presence`: `backend/core/online_status.py`; `backend/apps/users/presentation/views/users_views.py`; `frontend/src/composables/useOnline*.ts`; `frontend/src/lib/onlinePresence*`
- `W-api-client`: `frontend/src/api/client.ts`; `frontend/src/api/client.test.ts`; `frontend/src/router/index.ts`; `backend/config/middleware.py`; `backend/config/urls.py`

## Документы

### `CHAT_SYSTEM_DIAGNOSTIC.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Вступление / документ без заголовка | Complete chat system diagnostic and redesign notes | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |

### `FEED-JOURNAL.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| FEED JOURNAL - closed defects (from session) | FEED-001 BLOCKER F1: client_post_id idempotency - fixed in serializer + view (guard returns existing post). Verified by syntax check. | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Blocked / not fully verified (need runtime / DB / frontend build): | FEED-005 MED F5: migration 0006_feed_client_post_index.py added (AddIndex client_post_id+status). Needs `migrate`. | D0005, D0006, D0007, D0009 | W-post, W-checks |  |

### `FEED_AUDIT_ROUND1.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Лента - Аудит и исправления (раунд 1) | Параметры: CDN локальный (volume), ffmpeg разрешён, public_id 8-значные (UUIDv8Model), лимиты 500МБ/10МБ/1ГБ, бэкап не требуется пользовател… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Этап 1 - Карта (кратко) | Модели постов/ленты: backend/apps/social/infrastructure/models/social.py (Post, PostMedia, PostAttachment, PostComment, PostLike, Repost, Bo… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Реестр дефектов (компактно, ключевые) | Таблица значений или сценариев. | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Исправления (по одному, с проверкой) | FEED-001: feed_service.py - заменил offset/limit на cursor (created_at,id) + order_by '-created_at','-id'. Синтаксис OK. Проверка: запрос с… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Не исправлено / блокеры | F2 ленивое видео и F9 утечки: требуется чтение фронтенда (frontend/src) - не выполнено из-за токенов; рекомендую отдельный проход. | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Действия для пользователя (точный порядок) | Добавить ffmpeg в Dockerfile (backend, celery_worker, celery_beat) и пересобрать образы (пользователь разрешил). | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Не проверено (без запуска приложения / фронта) | Реальное время создания поста (≤300мс, ≤100мс оптимистично) | D0005, D0006, D0007, D0009 | W-post, W-checks |  |

### `FINAL_REPORT_SYNC_FAVORITES.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Вступление / документ без заголовка | ОТЧЁТ: синхронизация избранного (круг 1, ограничение токенов) | D0003, D0004 | W-favorites, W-notif |  |

### `NOTIF_REPORT_FINAL.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Вступление / документ без заголовка | ИТОГОВЫЙ ОТЧЁТ - уведомления animecore (2026-10-08) | D0013, D0015 | W-notif |  |

### `PROBLEM_SUMMARY.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Проблема и исправления (аниме-сайт / обсуждения) | Объединяет перечисленные подразделы. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| 1. Исходная ошибка - WebSocket 403 / HTTP 404 при открытии обсуждений | Причина:** сериализатор отдаёт `id` как `public_id` (`UUIDv8Model`). Фронт передаёт `public_id` в URL (`/ws/chat/96685756/`, `/social/chats/… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| 2. Вторичная ошибка - «Загрузка...» бесконечная при переключении чатов | Причина:** `apiClient.get()` (`frontend/src/api/client.ts`, строка 26) имеет `timeout: 300000` (5 минут). При навигации `router/index.ts` ст… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Остаточная проблема (если всё ещё висит после `Ctrl+F5`) | Если после жёсткой перезагрузки (`Ctrl+F5`) «Загрузка...» всё ещё висит дольше 10 сек - проверь в DevTools → Network конкретный URL (`pendin… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |

### `PRIVATE_NOTES.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Вступление / документ без заголовка | animecore /chats/{id} hangs. ChatDetailView.vue loadChat (~line 1558) conflicts with apiClient interceptor (frontend/src/api/client.ts 30-55… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |

### `README.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| AniSphere (animecore) | Платформа-каталог аниме: Django REST API + Celery + MySQL/Redis на бэкенде и Vue 3 + Vite SPA (PWA) на фронте. Данные каталога - Kodik (плюс… | D0001, D0002, D0008 | W-env, W-runtime, W-release |  |
| Структура проекта | Важно: весь проект использует **один** `.env` в корне. Другие `.env` создавать не нужно: | D0002 | W-env, W-runtime |  |
| Требования | Docker + Docker Compose (основной способ запуска); | D0002 | W-runtime |  |
| Настройка окружения | Все переменные находятся в `animecore/.env`. Обязательные секции: | D0002 | W-env, W-runtime |  |
| Запуск | Объединяет перечисленные подразделы. | D0001, D0002, D0008 | W-env, W-runtime, W-release |  |
| Способ 1. Docker (основной) | Запустятся 4 сервиса: | D0001, D0002, D0008 | W-env, W-runtime, W-release |  |
| Способ 2. Вне Docker | Бэкенд.** В `backend/` нужен venv с зависимостями (см. `requirements.txt` выше): | D0001, D0002, D0008 | W-env, W-runtime, W-release |  |
| Команды фронтенда | Скрипты из `frontend/package.json` (запускать из `frontend/`): | D0009 | W-runtime, W-checks |  |
| Миграции и superuser | Django Admin: `http://127.0.0.1:8000/admin/`. | D0004 | W-release |  |
| Импорт данных | Основной источник каталога - Kodik. Импорт асинхронный (Celery): эндпоинты только стартуют задачу, прогресс запрашивается отдельным GET. | D0017 | W-kodik, W-chat |  |
| Из админки фронтенда | Страница админ-панели: `frontend/src/components/page/admin/KodikImport.vue` (маршрут → `KodikImport`), а также `AdminDashboard.vue`. По сути… | D0017 | W-kodik, W-chat |  |
| API (эндпоинты импорта, `backend/config/urls.py`) | Пример: | D0017 | W-kodik, W-chat |  |
| Периодические импорты (Celery beat) | В `backend/config/celery.py` расписание: | D0017 | W-kodik, W-chat |  |
| Одиночный импорт аниме | `POST /api/anime/import-from-kodik/` (`backend/apps/anime/presentation/urls.py`, `KodikImportView`) - импорт/обновление одного тайтла по Kod… | D0017 | W-kodik, W-chat |  |
| CLI (внутри контейнера или venv) | Дампы Kodik хранятся в `backend/data/kodik_dumps` (внутри Docker: `/app/data/kodik_dumps`). | D0017 | W-kodik, W-chat |  |
| Импорт/экспорт настроек чата | (см. `backend/apps/social` - `SettingsExport`, передача JSON-экспорта между аккаунтами). | D0017 | W-kodik, W-chat |  |
| Основные API-эндпоинты | Полные справочники внешних API: `docs/KODIK_API/`, `docs/SHIKIMORI_API/`. | D0003 | W-anime, W-chat, W-post, W-notif |  |
| Проверка / линт | Бэкенд: в репозитории нет настроенных тестов/линтера (`conftest.py` исторически присутствовал, файлов `test_*.py` нет). Базовая проверка - з… | D0009 | W-runtime, W-checks |  |
| Типичная первая установка (шпаргалка) | Команды или пример контракта. | D0001, D0002, D0008 | W-env, W-runtime, W-release |  |

### `ROADMAP_30_ERRORS.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Точечная цель исправления 30 новых ошибок (таблица 2026-10-08 21:33) | Цель: goal-475f2b8e-b635-4289-ac1f-52b046af642b | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Итоговая проверка раунда 4 (2026-10-08 21:43) | A2 (client_message_id)** - FIXED (DB + ORM `Message` + `MessageSerializer`) | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |

### `ROADMAP_ERRORS_FIX.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Roadmap исправления ошибок `anisphere_backend` (по таблице 107 строк) | Активность: 2026-10-08. Источник: таблица ошибок (№ 1–107), backend - `anisphere_backend`. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Итоговая кластеризация (по корневым причинам) | Таблица значений или сценариев. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Фазы исправления (приоритет: A → B → C → D → F, E исправится сам после A+C) | Объединяет перечисленные подразделы. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Фаза 1 - Схема БД (критично, блокирует всё соц. и чат) - 1–2 дня | Цель:** устранить `Unknown column` и `Table doesn't exist`. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Фаза 2 - Сериализаторы (блокирует сообщения чата) - 0.5 дня | Цель:** устранить `AssertionError` в `MessageSerializer`. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Фаза 3 - Сервис фида (блокирует `/feed/weighted/`) - 0.5 дня | Цель:** исправить `FeedGenerationService.get_feed_queryset()`. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Фаза 4 - Уведомления + профиль (предупреждения и 500) - 1 день | Цель:** устранить `ProgrammingError` уведомлений и `Profile settings load failed`. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Фаза 5 - Каскадные 500 в соц. чатах и группах (следствие A+C) - 0.5 дня | Цель:** убедиться, что после Фазы 1+2 отсутствуют оставшиеся `Internal Server Error`. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Быстрые команды для проверки (для разработчика) | Команды или пример контракта. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Приоритетный порядок работ (кратко для исполнителя) | Миграции БД** (A + B) - без этого остальные шаги бесполезны; это 90% ошибок. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Связанные артефакты в рабочем каталоге | `defect_registry.txt` - CHAT-001…CHAT-006 (соц. чат, `public_id`, `seq`, `on_commit`). | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Проверка покрытия: исправляются ли все ошибки по родмапу? | Вывод: да, все 107 ошибок покрываются фазами 1–5.** | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Анализ по кластерам (ссылки на № из таблицы) | Таблица значений или сценариев. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Полная таблица ошибок (№ 1–107) с покрытием родмапом | Таблица значений или сценариев. | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Итоговая проверка по родмапу (для исполнителя) | Выполнить Фазу 1 (миграции)** → устранится ~80% ошибок (все A + B, плюс каскады E). | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |
| Дополнение (новая таблица, 30 строк, 2026-10-08 21:33) | Новые корневые ошибки из свежего лога - не покрыты предыдущими фазами: | D0003, D0004, D0009 | W-release, W-chat, W-post, W-notif |  |

### `SEO_JOURNAL.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Вступление / документ без заголовка | SEO-РЕАЛИЗАЦИЯ - ЖУРНАЛ ЭТАПОВ | D0010 | W-seo |  |

### `SEO_STATUS.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Вступление / документ без заголовка | S1–S8 СТАТУС (раунд 5) - до / после / осталось | D0010 | W-seo |  |

### `TASK.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Вступление / документ без заголовка | ЗАДАЧА | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |

### `backend/apps/anime/presentation/indexnow_template.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| IndexNow (Яндекс + Bing) - отправка URL после изменения | Объединяет перечисленные подразделы. | D0010 | W-seo |  |
| Требует API-ключ из .env (INDEXNOW_KEY) | Объединяет перечисленные подразделы. | D0010 | W-seo |  |
| Дедупликация через Redis (ключ indexnow:{url}, TTL 24ч) | Объединяет перечисленные подразделы. | D0010 | W-seo |  |
| Endpoint: https://www.indexnow.org/indexnow | Объединяет перечисленные подразделы. | D0010 | W-seo |  |

### `backend/apps/anime/presentation/seo_templates.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| SEO-шаблоны хабов - подстановка из данных БД, без фейков | Объединяет перечисленные подразделы. | D0010 | W-seo |  |
| title: «Аниме жанра «{name}» - лучшие тайтлы {year} \| {site}» (≤60) | Объединяет перечисленные подразделы. | D0010 | W-seo |  |
| desc: «Аниме жанра {name}: {count} тайтлов, от {min_rating} до {max_rating}. Топ: {top3}. Смотреть онлайн.» (140–160) | Объединяет перечисленные подразделы. | D0010 | W-seo |  |
| noindex если count < 5 | Объединяет перечисленные подразделы. | D0010 | W-seo |  |
| robots: index,follow или noindex,follow | Объединяет перечисленные подразделы. | D0010 | W-seo |  |

### `backend/seo_templates.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| SEO-шаблоны хабов (S2) - в однм конфиге, переопределяются в админке | Объединяет перечисленные подразделы. | D0010 | W-seo |  |
| Формат подстановки: {count}, {name}, {top3}, {year}, {site} | genre_hub: | D0010 | W-seo |  |

### `docs/CHAT_SYSTEM_REBUILD_PLAN.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| План полной переделки системы чатов AniSphere | Дата: 9 октября 2026 года. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| 1. Основание и границы исследования | Изучены модели чатов и сообщений, сериализаторы, маршруты REST и WebSocket, consumers, сервисы прав и кэша, прочтения, фоновые задачи, созда… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| 2. Обнаруженные проблемы | Объединяет перечисленные подразделы. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Идентификация и маршрутизация | Сериализаторы личных и групповых чатов отдают `public_id` под именем `id`, тогда как сообщения, часть actions, кэши и события используют вну… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Сообщения, права и гонки | Message.seq вычисляется через `MAX(seq) + 1`, без блокировки строки чата и уникальности пары «чат - seq». Параллельные отправки допускают од… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Прочтения, удаление и синхронизация | REST/модели используют MessageReadStatus, а WebSocket mark_messages_read обновляет Message.read_at. У изученной модели Message такого поля н… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Интерфейс и производительность | Состояние сообщений одновременно живёт в ChatDetailView, privateChat store и отдельном FranchiseDiscussionChat; списки обновляются из нескол… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Фоновые задачи и тесты | В tasks_chat задачи объявлены `bind=True`, но функции не принимают self; это несовместимость сигнатур связанных задач. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| 3. Целевая архитектура | Сохраняем Django/DRF, Channels, MySQL, Redis, Celery, Vue 3 и TypeScript. Основное изменение - единая предметная модель и единый путь измене… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| 4. Порядок реализации | Объединяет перечисленные подразделы. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 0. Фиксация исходного состояния | Зафиксировать текущий diff и выделить ветку реализации, сохранив существующие пользовательские изменения. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 1. Контракты и правила поведения | Составить таблицу «сущность → команда → роль → изменение БД → событие → результат UI» для всех функций. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 2. Новая схема и перенос данных | Создать Conversation и новые FK, таблицу соответствий старого type/PK/public_id/code/slug новому публичному ID. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 3. Ядро операций и права | Реализовать сервисы создания/получения чата, управления группой, участниками, ролями, темами, настройками и папками. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 4. Сообщения и файлы | Отправка: проверка прав и содержимого → захват счётчика чата → выдача seq → Message + attachments + outbox в одной транзакции. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 5. Прочтения и производные данные | Хранить прочтения в MySQL; использовать монотонный read cursor по чату/теме с отдельно определённым поведением для непросмотренных промежутк… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 6. Надёжная доставка событий | Записывать событие в той же транзакции, что состояние. После commit запускать доставку; outbox worker с повтором сохраняет события при недос… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 7. Frontend и интерфейс | Перенести операции из компонентов в единый data layer; удалить несогласованные типы, window events и дублирующие массивы после перевода потр… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 8. Остальные функции | Приглашения/заявки: атомарная проверка и расход лимита, срок, отзыв, target_user, роль, вместимость, повтор заявки, одобрение/отклонение, пр… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 9. Производительность и наблюдаемость | Определить нагрузочный профиль из фактического использования: одновременные пользователи, активные группы, сообщения/секунду, размер истории… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 10. Проверки | Backend unit/contract: точные статусы/DTO, policies, валидация, ограничения БД, все CRUD и side effects. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Этап 11. Переключение и завершение | Разворачивать по feature flag: новая схема → миграция копии → новые сервисы/API → новый UI → контрольная сверка → включение. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| 5. Обязательная матрица приёмки | Каждая строка проходит для допустимых ролей и отдельно проверяется на отказ доступа. Критерий «готово» - совпадение сохранённого состояния и… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| 6. Последовательность поставок | Baseline, спецификация и regression cases для найденных дефектов. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
### `docs/CHAT_SYSTEM_REBUILD_STATUS.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Переделка чатов: состояние реализации | Состояние реализации на октябрь 2026 года. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks | |
| Реализовано | Общая Conversation, типизированные публичные ID, последовательности/version, ограничения БД и идемпотентные команды. HTTP, WS и scheduled wo… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Проверки | Следующая таблица сохраняет результаты первой приёмки. Актуальная общая проверка после исправления блокеров: **165 backend-тестов, 14 Vitest… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Локальный выпуск | По уточнению пользователя целевой стенд - localhost. Автономные образы пересобраны через официальный registry, общие type-check/миграционные… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Обслуживание файлов | Аудит при работающем приложении: `python manage.py gc_chat_files --older-than-hours 24 --limit 100`. Для apply сначала проверенная резервная… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Переключение и восстановление | Новому коду нужны **миграции 0019–0026**. Нельзя запускать новый backend/worker поверх старой схемы или оставлять старый worker пишущим посл… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |

### `docs/CHAT_UI_FIXES_2026-10-10.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Исправления интерфейса чатов - 10 октября 2026 | Локальная сборка: http://localhost:8080. Миграция `social/0028_chat_card_radii` добавляет хранение скругления карточек аниме и плейлистов. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Изменения по замечаниям | Личный чат использует установленный аватар собеседника из `other_user.avatar_url` в списке и заголовке. Учтены ответы API, где `user1`/`user… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Проверки | серверных тестов прошли на отдельной MySQL: 10 новых регрессий, 31 тест расширений, 45 тестов ядра и управления. Логи: `backend/data/local_r… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Настоящие карточки в превью | Превью темы и обоев использует общий `ChatContentCard` и общий CSS с реальными сообщениями. Пример аниме - оригинальный «Ван-Пис» 1999 года… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Очистка существующих чатов | Перед очисткой останавливаются записывающие процессы, сохраняются SQL и общие/приватные медиа с SHA-256. SQL восстанавливается в отдельную M… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Повторная проверка карточек и истории личного чата | Исправлены два воспроизведённых дефекта: | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Онлайн и участие в обсуждениях | Статус онлайн теперь связан с глобальными WebSocket-соединениями. Реестр соединений хранится в Redis и общий для ASGI-процессов. Закрытие од… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |

### `docs/CHAT_UI_FIXES_2026-10-11.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Исправления чатов - 11 октября 2026 | Локальный выпуск: http://localhost:8080. Предыдущие изменения и резервная копия сохранены. Этот выпуск не очищает пользовательские чаты. | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Изменения | Поле сообщения сохраняет фокус при отправке через Enter и возвращает его после нажатия кнопки. Во время сохранения очереди поле становится r… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Проверки | серверных тестов на изолированной MySQL: ядро, расширения, интерфейсные регрессии, присутствие и восемь новых сценариев. Лог: `backend/data/… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Дополнение: поиск и отправленные фотографии | Между карточками результатов теперь 12 px, внутренние отступы - 12 px. Карточки не сжимаются при длинном списке: в браузере до исправления в… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |
| Границы постеров в результатах поиска | Карточка имеет минимальную высоту `60px + 1.5rem + 2px`, учитывающую постер, оба внутренних отступа и границы. Высота может увеличиваться дл… | D0003, D0005, D0009, D0016 | W-chat, W-presence, W-api-client, W-checks |  |

### `docs/KODIK_API/API.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Документация по API | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| API-токен | Ваш API-токен: `74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |
| Описание | API предназначено для удобного получения любой информации из нашей базы. | D0017 | W-kodik |  |
| Ресурсы | На данный момент доступно три типа ресурсов: | D0017 | W-kodik |  |
| Документация по ресурсам | Документация по `/years` | D0017 | W-kodik |  |

### `docs/KODIK_API/AUTO_ADD.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Скрипт для автоматического добавления плееров | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| Описание | Данный скрипт позволяет автоматически разместить плеер на всех страницах вашего сайта. Плеер будет отображаться только на тех страницах для… | D0017 | W-kodik |  |
| Генератор конфигурации | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Код скрипта (автогенерация на основе параметров выше): | Копировать** | D0017 | W-kodik |  |
| Код iframe (автогенерация на основе параметров выше): | Iframe вариант кода нужен только для тех, кто по какой-то причине не может использовать обычный скрипт. Iframe вариант менее гибкий из-за то… | D0017 | W-kodik |  |
| Параметры | Параметры указываются в переменной-объекте `kodikAddPlayers`. Все параметры являются необязательными. | D0017 | W-kodik |  |
| Пример | Копировать** | D0017 | W-kodik |  |

### `docs/KODIK_API/DATABASE.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Файлы со всеми фильмами, сериалами, роликами | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| Описание | Файлы созданы для удобного парсинга базы программами или скриптами. | D0017 | W-kodik |  |
| Аниме фильмы | `https://dumps.kodikres.com/films/anime.json?token=74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |
| Аниме сериалы | `https://dumps.kodikres.com/serials/anime-serial.json?token=74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |
| Выгрузки с Shikimori: | Календарь `https://dumps.kodikres.com/calendar.json?token=74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |

### `docs/KODIK_API/DOMAIN_REPLACE.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Скрипт для замены домена во всех плеерах | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| Описание | Скрипт предназначен для случая, если вам нужно будет максимально быстро сменить на сайте все домены плееров на другие. | D0017 | W-kodik |  |
| Генератор конфигурации | Копировать** | D0017 | W-kodik |  |
| Параметры | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Пример | Копировать** | D0017 | W-kodik |  |

### `docs/KODIK_API/FAQ.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| FAQ | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| Вопросы | На данной странице собраны самые популярные и важные вопросы касающиеся работы с базой. Со временем вопросы будут дополняться. Если вам все… | D0017 | W-kodik |  |
| Как добавляются материалы в базу? | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| АНИМЕ | Основной источник информации: World-Art. Второстепенный источник: Shikimori. | D0017 | W-kodik |  |
| ФИЛЬМЫ, СЕРИАЛЫ, ДОРАМЫ | Основной источник информации: KinoPoisk. Второстепенные источники: IMDb, MyDramaList | D0017 | W-kodik |  |
| Как определяется что материал является аниме? | Если принадлежность к аниме не очевидна, то она определяется по следующим правилам: | D0017 | W-kodik |  |
| Какие материалы добавляются в базу? | База специализируется в первую очередь на контенте восточных стран: аниме, дорамы, турецкие/индийские/бразильские сериалы. | D0017 | W-kodik |  |
| Как получить ссылку на серию? | Существует множество способов получения ссылок на конкретные сезоны или эпизоды: | D0017 | W-kodik |  |
| Что делать если в каком-то материале ошибка / материал требует обновления? | Если вы заметили ошибку в добавленном в базу материале, то самое простое, это в таблице с материалами справа нажать на иконку треугольника с… | D0017 | W-kodik |  |
| Как добавить сайт? | Для того, чтобы добавить в свой профиль сайт, нужно зайти в настройки слева в меню и там выбрать раздел "Добавление сайта". Там вы сможете д… | D0017 | W-kodik |  |
| Что такое "ссылка на страницу" / "страница для соц сетей"? | При копировании плееров из базы вы могли заметить сверху справа опцию "ссылка на страницу". | D0017 | W-kodik |  |
| Как найти нужный материал? | Для поиска материала в базе, вы можете воспользоваться поиском в базе. По умолчанию он ищет по названиям (по всем названиям, которые мы знае… | D0017 | W-kodik |  |
| Как добавить плеер на сайт? | Добавить плеер на сайт можно множеством разных способов. Для начала вам нужно определиться, что именно вы хотите сделать. | D0017 | W-kodik |  |
| Как парсить последние серии? | Для получения информации по последним сериям вы можете использовать метод API list. Там по умолчанию включена сортировка по дате обновления.… | D0017 | W-kodik |  |
| Есть ли лимиты запросов к API? | Лимитов запросов к API нет, но рекомендуется в любом случае оптимизировать работу с API: | D0017 | W-kodik |  |

### `docs/KODIK_API/IFRAME.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Параметры iframe | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| Описание | В данной инструкции описываются параметры, добавляемые к ссылке на плеер. Сами параметры добавляются после вопросительного знака (`?`), но е… | D0017 | W-kodik |  |
| Параметры: | Скрытие плеера для определенных стран | D0017 | W-kodik |  |
| Скрытие плеера для определенных стран | Также вы можете глобально заблокировать все плееры на вашем сайте для какой то страны (или стран) в настройках плеера. | D0017 | W-kodik |  |
| Отключение выбора озвучек в сериале или сезоне | Также вы можете глобально отключить выбор озвучек для всех плееров на вашем сайте в настройках плеера. | D0017 | W-kodik |  |
| Скрытие определенных озвучек в селекторе | Также вы можете глобально скрыть определенные озвучки в селекторе для всех плееров на вашем сайте в настройках плеера. | D0017 | W-kodik |  |
| Показ только определенных озвучек в селекторе | Также вы можете настроить это глобально для всех плееров в настройках плеера. | D0017 | W-kodik |  |
| Автоматический выбор озвучки | Также вы можете настроить это глобально для всех плееров в настройках плеера. | D0017 | W-kodik |  |
| Выбор серии и сезона | Также вы можете глобально настроить выбираемую серию и сезон для всех плееров на вашем сайте в настройках плеера. | D0017 | W-kodik |  |
| Показать только плеер конкретной серии или конкретного сезона в сериале | Каждая серия или сезон имеет свою собственную ссылку и свой собственный плеер, которые можно взять либо кликнув по кнопке "сезонов" в базе,… | D0017 | W-kodik |  |
| Скрытие селекторов в плеере (сезон, серия, озвучка) | От параметра `only_episode` этот параметр отличается тем, что не отключает функционал выбора серии и сезона, а только скрывает видимость это… | D0017 | W-kodik |  |
| Скрытие кнопки "продолжить просмотр" | Чтобы скрыть кнопку "продолжить просмотр" для конкретного плеера вам надо в ссылке на плеер добавить параметр `hide_resume_button` и установ… | D0017 | W-kodik |  |
| Выбор времени старта | С помощью данной настройки можно выбрать с какого времени плеер будет стартовать. Обычно мы сами устанавливаем подобный параметр для фильмов… | D0017 | W-kodik |  |
| Кнопка пропуска опенинга/эндинга | Данный параметр позволяет добавить в плеер кнопку пропуска определенного интервала (например опенинга или эндинга). | D0017 | W-kodik |  |
| Постер | Если вам нужно установить одинаковый постер на все плееры, то сделать это лучше через настройки плеера в соответствующем разделе. | D0017 | W-kodik |  |
| Предупреждение о минимальном возрасте | Вы можете глобально включить для всех плееров иконки в превью/плеере или подтверждение возраста для материалов с 18+ рейтингом в настройках… | D0017 | W-kodik |  |
| Предупреждение о LGBT контенте | Вы можете глобально включить для всех плееров иконки в превью или предупреждение для материалов с LGBT контентом в настройках плеера. | D0017 | W-kodik |  |

### `docs/KODIK_API/PLAYER_API.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Документация по API плеера | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| Описание | Благодаря API плеера вы можете получать актуальную информацию во время воспроизведения, а также управлять плеером с помощью javascript на св… | D0017 | W-kodik |  |
| Получение информации | Для получения информации нужно добавить функцию обработчик входящих сообщений. `message.data` при этом будет содержать два параметра: `key`… | D0017 | W-kodik |  |
| Управление плеером | Для управления плеером необходимо через `postMessage` передавать iframe элементу плеера команды в определенном формате. | D0017 | W-kodik |  |

### `docs/KODIK_API/api/COUNTRIES.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Документация по API: /countries | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| API-токен | Ваш API-токен: `74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |
| Описание | Возвращает список всех возможных стран либо для всех материалов, либо для материалов отфильтрованных вашими параметрами. Учитываются только… | D0017 | W-kodik |  |
| Параметры | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Стуктура ответа | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Примеры использования | `https://kodik-api.com/countries?token=74ecb013335271e4344ebc994956dd75&types=anime-serial` | D0017 | W-kodik |  |

### `docs/KODIK_API/api/GENRES.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Документация по API: /genres | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| API-токен | Ваш API-токен: `74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |
| Описание | Возвращает список всех возможных жанров либо для всех материалов, либо для материалов отфильтрованных вашими параметрами. Учитываются только… | D0017 | W-kodik |  |
| Параметры | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Стуктура ответа | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Примеры использования | `https://kodik-api.com/genres?token=74ecb013335271e4344ebc994956dd75&types=anime-serial` | D0017 | W-kodik |  |

### `docs/KODIK_API/api/LIST.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Документация по API: /list | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| API-токен | Ваш API-токен: `74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |
| Описание | Возвращает список всех материалов, подходящих под критерии запроса, либо вообще всех, если критерии не указаны. | D0017 | W-kodik |  |
| Параметры | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Стуктура ответа | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Примеры использования | `https://kodik-api.com/list?token=74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |
| Стуктура информации КиноПоиска, Shikimori, MyDramaList | При отсутствии информации кинопоиска, shikimori и mydramalist для какого-либо материала, поле `material_data` будет отсуствовать. | D0017 | W-kodik |  |

### `docs/KODIK_API/api/QUALITIES-V2.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Документация по API: /qualities/v2 | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| API-токен | Ваш API-токен: `74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |
| Описание | Возвращает список всех возможных качеств либо для всех материалов, либо для материалов отфильтрованных вашими параметрами. | D0017 | W-kodik |  |
| Параметры | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Стуктура ответа | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Примеры использования | `https://kodik-api.com/qualities/v2?token=74ecb013335271e4344ebc994956dd75&types=anime-serial` | D0017 | W-kodik |  |

### `docs/KODIK_API/api/SEARCH.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Документация по API: /search | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| API-токен | Ваш API-токен: `74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |
| Описание | Возвращает список наиболее подходящих вашему поисковому запросу материалов. Наиболее релевантные материалы будут идти первыми. | D0017 | W-kodik |  |
| Параметры | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Стуктура ответа | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Примеры использования | `https://kodik-api.com/search?token=74ecb013335271e4344ebc994956dd75&title=Аватар%20смотреть%20онлайн%20бесплатно` | D0017 | W-kodik |  |
| Стуктура информации КиноПоиска, Shikimori, MyDramaList | При отсутствии информации кинопоиска, shikimori и mydramalist для какого-либо материала, поле `material_data` будет отсуствовать. | D0017 | W-kodik |  |

### `docs/KODIK_API/api/TRANSLATIONS-V2.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Документация по API: /translations/v2 | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| API-токен | Ваш API-токен: `74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |
| Описание | Возвращает список всех возможных озвучек либо для всех материалов, либо для материалов отфильтрованных вашими параметрами. | D0017 | W-kodik |  |
| Параметры | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Стуктура ответа | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Примеры использования | `https://kodik-api.com/translations/v2?token=74ecb013335271e4344ebc994956dd75&types=anime-serial` | D0017 | W-kodik |  |

### `docs/KODIK_API/api/YEARS.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Документация по API: /years | Объединяет перечисленные подразделы. | D0017 | W-kodik |  |
| API-токен | Ваш API-токен: `74ecb013335271e4344ebc994956dd75` | D0017 | W-kodik |  |
| Описание | Возвращает список всех возможных годов либо для всех материалов, либо для материалов отфильтрованных вашими параметрами. Учитываются только… | D0017 | W-kodik |  |
| Параметры | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Стуктура ответа | Таблица значений или сценариев. | D0017 | W-kodik |  |
| Примеры использования | `https://kodik-api.com/years?token=74ecb013335271e4344ebc994956dd75&types=anime-serial` | D0017 | W-kodik |  |

### `docs/LOCAL_RELEASE_REPORT.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Локальный выпуск и проверка чатов | октября 2026 года. Адрес: **http://localhost:8080**. По указанию пользователя все работы выполнены локально. DEBUG выключен; backend, Celery… | D0004, D0008, D0009 | W-release, W-checks, W-chat, W-post |  |
| Исправленные блокеры | Backend/frontend собираются через официальный `registry-1.docker.io/library/*`, обходя настроенные зеркала с HTTP 403. Глобальные настройки… | D0004, D0008, D0009 | W-release, W-checks, W-chat, W-post |  |
| Проверки | Наборы, использующие одну тестовую БД, запускаются последовательно. Браузер использовал временные учётные записи в рабочей локальной БД; пос… | D0004, D0008, D0009 | W-release, W-checks, W-chat, W-post |  |
| Профиль задержек | Измеряется фактическая собранная версия через http://localhost:8080: 100 личных чатов, 100000 сообщений в одном из них, 10 прогревочных запр… | D0009 | W-chat, W-checks |  |
| Сохранность и восстановление | Перед обновлением сохранён dump `backend/data/local_release/20261010-095453/database.sql`: 81015200 байт, SHA-256 `5a8857ac5f1b59224c661398d… | D0004 | W-release |  |
| Воспроизведение | Запуск локальной сборки: | D0004, D0008, D0009 | W-release, W-checks, W-chat, W-post |  |

### `docs/POST_SYSTEM_REBUILD_PLAN.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| План исправления системы постов | октября 2026 года. План составлен после реализации и локальной приёмки чатов. При подготовке локальной сборки исправлены общие блокеры и баз… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Цель и границы | Обеспечить корректное создание, чтение, изменение и удаление постов и связанных данных. Охват: личная/публичная лента, подписки, страницы по… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Исходный baseline до исправлений | Изолированная MySQL 8; `config.settings_chat_test`; команда: | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Карта изменений | Таблица значений или сценариев. | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Правила новой реализации | Доступ.** Одна функция доступных постов и одно правило операции. Guest видит опубликованные публичные посты публичной группы; followers - те… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Этапы реализации | Объединяет перечисленные подразделы. | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| 0. Воспроизведение и защита данных - P0 | Сохранить SQL/медиа и fingerprints постов/комментариев/связей; проверить restore на отдельной MySQL. В основной БД выполнить только read-onl… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| 1. Права доступа и безопасный вывод - P0 | Общая выборка доступных записей и проверки авторства/ролей до изменения. Перевести retrieve, public_retrieve, все ленты/фильтры, comments, r… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| 2. CRUD, версия и идемпотентность - P0/P1 | Вынести сервисы и serializers постов из общего файла; оставить тонкие view. Объединить update/edit и soft delete. | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| 3. Вложения и обработка медиа - P0/P1 | Один upload pipeline для create/edit; явно различать «поле отсутствует», «удалить все» и «заменить список». | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| 4. Комментарии и действия - P1 | Единый контракт root/reply с ограниченной пагинацией. Родитель должен принадлежать тому же доступному посту; запрет циклов и явный предел гл… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| 5. Лента, события, кеши и уведомления - P1/P2 | Стабильная сортировка и cursor по published_at/id; pinned отдельно без дублей. Weighted feed формирует одну страницу со стабильным снимком р… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| 6. Frontend и сборка - P1/P2 | Объединить типы FeedPost/PostComment/Media и нормализацию; убрать any и разнородные response adapters. | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| 7. Миграции, приёмка и переключение - P1 | Read-only `audit_posts`/`posts_health`: связи, ID, дубли команд, counters, файлы, backlog/lease, версии. Ремонт данных - отдельный dry-run и… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Матрица приёмки | Нагрузочный профиль: сначала зафиксировать baseline, затем 100 000 постов, страница 20–50, 200 клиентов и конкурентные действия; измерять SQ… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |
| Порядок и контроль завершения | Выполнять этапы последовательно: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7. UI-контракт согласовать на этапе 0, обновлять вместе с API. Первые изменения… | D0005, D0006, D0007, D0009 | W-post, W-checks |  |

### `docs/SHIKIMORI_API/animes/ANIMES.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| GET /api/animes | List animes | D0001 | W-shikimori |  |
| Примеры | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| GET /api/animes | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| 200 | Команды или пример контракта. | D0001 | W-shikimori |  |
| Параметры | Таблица значений или сценариев. | D0001 | W-shikimori |  |

### `docs/SHIKIMORI_API/animes/ANIMES_ID.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| GET /api/animes/:id | Show an anime | D0001 | W-shikimori |  |
| Примеры | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| GET /api/animes/50 | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| 200 | Команды или пример контракта. | D0001 | W-shikimori |  |

### `docs/SHIKIMORI_API/animes/ANIMES_ID_FRANCHISE.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| GET /api/animes/:id/franchise | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| Примеры | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| GET /api/animes/46/franchise | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| 200 | Команды или пример контракта. | D0001 | W-shikimori |  |

### `docs/SHIKIMORI_API/animes/ANIMES_ID_SIMILAR.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| GET /api/animes/:id/similar | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| Примеры | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| GET /api/animes/44/similar | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| 200 | Команды или пример контракта. | D0001 | W-shikimori |  |

### `docs/SHIKIMORI_API/calendar/CALENDAR.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| GET /api/calendar | Show a calendar | D0001 | W-shikimori |  |
| Примеры | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| GET /api/calendar | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| 200 | Команды или пример контракта. | D0001 | W-shikimori |  |
| Параметры | Таблица значений или сценариев. | D0001 | W-shikimori |  |

### `docs/SHIKIMORI_API/constants/CONSTANTS.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| GET /api/constants/anime | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| Примеры | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| GET /api/constants/anime | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| 200 | Команды или пример контракта. | D0001 | W-shikimori |  |

### `docs/SHIKIMORI_API/episodes/EPISODE_NOTIFICATIONS.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| POST /api/v2/episode_notifications | Notify shikimori about anime episode release | D0001 | W-shikimori |  |
| Примеры | Объединяет перечисленные подразделы. | D0001 | W-shikimori |  |
| POST /api/v2/episode_notifications | Команды или пример контракта. | D0001 | W-shikimori |  |
| 200 | Команды или пример контракта. | D0001 | W-shikimori |  |
| Параметры | Таблица значений или сценариев. | D0001 | W-shikimori |  |

### `frontend/public/def_ava/README.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Дефолтные аватарки пользователей | Поместите ваши JPG/PNG изображения в эту папку. После сборки они автоматически попадут в `dist/def_ava/`. | TBD | W-default-avatars |  |
| Что нужно сделать | Загрузите свои аватарки** в папку `frontend/public/def_ava/` | TBD | W-default-avatars |  |
| Готово! | При регистрации новым пользователям будет автоматически назначаться случайная аватарка из списка. | TBD | W-default-avatars |  |

### `frontend/public/verification.README.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Файлы верификации для Google Search Console и Яндекс.Вебмастер | Объединяет перечисленные подразделы. | D0010 | W-seo, W-env |  |
| Создайте в .env: | Объединяет перечисленные подразделы. | D0010 | W-seo, W-env |  |
| GSC_VERIFICATION=google1234.html | Объединяет перечисленные подразделы. | D0010 | W-seo, W-env |  |
| YANDEX_VERIFICATION=yandex5678.html | Объединяет перечисленные подразделы. | D0010 | W-seo, W-env |  |
| Затем положите файлы в public/ ( фронт ) или отдайте Django static. | Объединяет перечисленные подразделы. | D0010 | W-seo, W-env |  |

### `frontend/src/assets/translation-avatars/INSTRUCTIONS.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Аватарки озвучек - Инструкция | Объединяет перечисленные подразделы. | D0014 | W-avatars |  |
| Что сделано | Создана система автоматического отображения аватарок для озвучек. Если у озвучки есть логотип в API, он отображается первым. Если нет - сист… | D0014 | W-avatars |  |
| Созданные аватарки | Уже созданы заглушки для популярных озвучек: | D0014 | W-avatars |  |
| Как добавить аватарку для новой озвучки | Объединяет перечисленные подразделы. | D0014 | W-avatars |  |
| 1. Узнайте название озвучки | Откройте страницу аниме и посмотрите список озвучек. | D0014 | W-avatars |  |
| 2. Нормализуйте название | Система автоматически преобразует название: | D0014 | W-avatars |  |
| 3. Создайте файл | Поместите файл в папку `frontend/src/assets/translation-avatars/` с нормализованным названием. | D0014 | W-avatars |  |
| 4. Поддерживаемые форматы | SVG (рекомендуется для заглушек) | D0014 | W-avatars |  |
| 5. Рекомендуемый размер | x200px для PNG/JPG | D0014 | W-avatars |  |
| Примеры | Если у вас есть озвучка "Мой Дуб" (My Dub), создайте файл: | D0014 | W-avatars |  |
| Как узнать, какой файл создать | Откройте консоль разработчика (F12) | D0014 | W-avatars |  |
| Замена существующих аватарок | Если вы хотите заменить существующую аватарку: | D0014 | W-avatars |  |
| Примечания | Если аватарка не найдена, отображаются инициалы озвучки | D0014 | W-avatars |  |

### `frontend/src/assets/translation-avatars/README.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Аватарки озвучек | В этой папке хранятся аватарки для озвучек аниме. | D0014 | W-avatars |  |
| Правила именования | Имя файла должно соответствовать названию озвучки в нижнем регистре, с заменой пробелов на дефисы и удалением специальных символов. | D0014 | W-avatars |  |
| Поддерживаемые форматы | PNG (рекомендуется) | D0014 | W-avatars |  |
| Размер | Рекомендуемый размер аватарки: 200x200px | D0014 | W-avatars |  |
| Пример использования | Если у озвучки есть аватарка в этой папке, она будет автоматически отображаться. | D0014 | W-avatars |  |

### `AGENTS.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Agent instructions | Объединяет перечисленные подразделы. | TBD | W-kms |  |
| Knowledge base | This project uses kms's fact/decision/guardrail/skill knowledge system. | TBD | W-kms |  |

### `docs/SEO_IMPLEMENTATION_2026-10-15.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Техническое SEO | Архитектура, политики страниц, администрирование, приватность, sitemap, проверка и внешние действия | D0028 | W-seo, W-env, W-checks | 2026-10-15 |

### `docs/NATIVE_APPLICATIONS.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Устанавливаемые приложения | Сборки по актуальному origin, кеши, ключи, ограничения IPA, ожидание MySQL | TBD | W-env, W-checks | 2026-10-16 |

### `docs/NATIVE_APPLICATIONS_REVIEW_2026-10-16.md`

| Раздел | Содержание | Решения | Watch paths | last-verified |
| --- | --- | --- | --- | --- |
| Проверка | Настоящие установщики и SHA-256, адаптивность, PiP и запуск Docker | TBD | W-env, W-checks | 2026-10-16 |

### `docs/SEO_UI_REPAIR_2026-10-16.md`

| Раздел | Содержание | Решения | Рабочие области | Проверено |
| --- | --- | --- | --- | --- |
| Восстановление UI после SEO | Общий каталог на подборках, темы, заголовок/футер, регрессионные проверки и ограничения измерений | D0028 | W-seo, W-checks | 2026-10-16 |
