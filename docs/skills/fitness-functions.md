---
id: fitness-functions
title: Инвентарь проверок и гейтов
status: active
date: '2026-10-11'
tags:
- knowledge-management
- verification
kms-generated: true
---

Статический инвентарь на 2026-10-11. Наличие сценария не означает текущий PASS; bootstrap приложение/БД/контейнеры не запускал. `.github/workflows` отсутствует.

| Правило | Реальный механизм | Решение | Проверенные источники |
| --- | --- | --- | --- |
| Type-check входит в образ frontend | frontend/Dockerfile → npm run build → vue-tsc + Vite; обязательный build gate | D0002, D0009 | F0005 |
| Backend/worker/beat ждут миграции и schema ready | Compose migrate dependency + docker_entrypoint; обязательный startup gate | D0004 | F0006; test_chat_startup.py |
| Public IDs, seq, повторы, версии и replay чатов | DB constraints, conversations service; unit/transport сценарии запускаются отдельно | D0003, D0005 | F0008; test_conversations.py, test_chat_integration.py |
| Права постов, version и outbox | post_access/post_commands и отдельные regression/transport сценарии | D0005, D0006 | F0009; test_site_rebuild.py, test_post_transport.py |
| Приватное медиа не входит в общий кэш | SW/nginx + privateMediaCache Vitest/browser; сценарии по запросу | D0007 | F0010; frontend/tests/chat-local-cache-browser.js |
| Срок приглашений 24h; общий бюджет 250 MiB | model/view + frontend/backend validator; backend/UI unit/browser | D0011, D0012 | F0012, F0013; test_chat_requested_fixes.py, chatUploadLimits.test.ts |
| Mute и изоляция аккаунтов | notification policy + library/composable tests | D0013 | F0014; chatNotificationPreferences.test.ts, useTabBadge.test.ts |
| Настройки чата ограничены размером | settings_transfer validation + test_chat_extensions.py | TBD | F0019 |
| GC по умолчанию dry-run и восстановимый карантин | validation команды, file_gc service, test_chat_file_gc.py | D0004 | F0020 |
| Backup/rehearsal и fingerprint | scripts/local_release_backup.py, site_rebuild_backup.py, site_rebuild_rehearsal.py; ручной запуск | D0004 | docs/LOCAL_RELEASE_REPORT.md; test_chat_extensions.py |
| p95 измеряется с профилем и временными данными | scripts/profile_local_chats.mjs; exit 2 при превышении предварительных 300/500 мс; ручной запуск | D0009 | F0018 |
| Загрузка и геометрия реального UI | Vitest + frontend/tests/chat-attachment-layout-browser.js и другие browser scripts; ручной запуск | D0009, D0016 | docs/CHAT_UI_FIXES_2026-10-11.md |

Неавтоматизированные правила и частичные гейты: `bootstrap-audit.md` (B10–B15). Команды, создающие фикстуры/резервные копии, - описанные механизмы, bootstrap их не выполнял.

Календарь/рекомендации: `test_calendar_recommendations.py` проверяет импорты, историю API, timezone, фильмы, сохранённые снимки и объяснения на отдельной MySQL (D0019–D0021, F0026–F0028). `RecommendationCard.test.ts`, `CalendarView.test.ts` и `frontend/tests/calendar-recommendations-browser.js` проверяют подсказки и навигацию. `scripts/verify_calendar_upgrade.py` проверяет миграции на полной копии базы; browser-фикстуры используют отдельную `calendar_browser_v1`, unit - `test_calendar_v1`.

Новые серии/подписки/напоминания: `test_episode_events.py` проверяет lifecycle, источник, фактический прогресс, доступ, перенос, DST, повторы и конкурентные доставки (D0022–D0024, F0029–F0031). `HomeView.test.ts`, `CalendarReleaseCard.test.ts`, `ReminderModal.test.ts` - UI unit. `episode-features-browser.js` и `episode-events-browser*.js` проверяют настоящий API, отдельную MySQL episode_browser_v1, Redis/WS и native Notification. `verify_episode_upgrade.py` сохраняет dump и проверяет старые поля на полной копии базы.

При подготовке общих коммитов 2026-10-12 сборка frontend прошла. Общий Vitest: 85/87 PASS; два теста `RecommendationCard.test.ts` ожидают закомментированную `.reason-btn`. Текущее поведение сохранено; подробности - `docs/EPISODES_REMINDERS_V1_2026-10-12.md`.
